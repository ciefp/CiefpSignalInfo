from Screens.ChannelSelection import ChannelSelection
from enigma import iServiceInformation, eTimer
from Screens.Screen import Screen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ActionMap import ActionMap
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists
import os

# ==== LOKALNI PiconManager ====
try:
    from .components.picon_manager import PiconManager
    HAS_PICON_MANAGER = True
except ImportError as e:
    HAS_PICON_MANAGER = False
    print(f"[CiefpSignalInfoMini] PiconManager not available: {e}")

PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo"


class CiefpSignalInfoMini(Screen):
    """Mini signal info - gore centrirano, osvežava se pri promeni kanala."""

    skin = """
    <screen name="CiefpSignalInfoMini" position="center,20" size="1000,160"
            backgroundColor="#0D1B36" flags="wfNoBorder">

        <!-- Tanki okvir oko celog mini skina -->
        <eLabel position="0,0" size="1000,160" backgroundColor="#0D1B36"
                borderWidth="2" borderColor="#00C000" zPosition="-1" />

        <!-- Picon (levo) -->
        <widget name="mini_picon" position="15,15" size="220,132"
                alphatest="blend" transparent="1" />

        <!-- SNR labela + traka -->
        <widget name="mini_snr_label" position="290,25" size="60,30"
                font="Bold;22" halign="left" valign="center"
                foregroundColor="#00FF00" transparent="1" text="SNR" />
        <widget name="mini_snr_bar" position="355,27" size="220,26"
                pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo/mini_snr.png"
                borderWidth="1" borderColor="#000000" />
        <widget name="snr_value" position="550,25" size="180,30"
                font="Bold;22" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
        <widget name="snr_db" position="550,110" size="340,30"
                font="Bold;26" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
                
        <!-- AGC labela + traka -->
        <widget name="mini_agc_label" position="290,75" size="60,30"
                font="Bold;22" halign="left" valign="center"
                foregroundColor="#00FF00" transparent="1" text="AGC" />
        <widget name="mini_agc_bar" position="355,77" size="220,26"
                pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo/mini_agc.png"
                borderWidth="1" borderColor="#000000" />
        <widget name="agc_value" position="550,75" size="180,30"
                font="Bold;22" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
        
        <widget name="channel_name" position="290,110" size="320,30"
                font="Bold;26" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
                
        <!-- Desna strana - 3 linije parametara -->
        <widget name="mini_line1" position="790,15" size="200,36"
                font="Bold;24" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
        <widget name="mini_line2" position="790,55" size="200,36"
                font="Bold;24" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
        <widget name="mini_line3" position="790,95" size="200,36"
                font="Bold;24" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />
    </screen>
    """

    def __init__(self, session, parent=None):
        Screen.__init__(self, session)
        self.parent = parent
        # === Kreiraj nevidljivu ChannelSelection instancu za navigaciju ===
        self.servicelist = None
        try:
            self.servicelist = self.session.instantiateDialog(ChannelSelection)
            print("[CiefpSignalInfoMini] ChannelSelection instantiated")
        except Exception as e:
            print(f"[CiefpSignalInfoMini] ChannelSelection init error: {e}")
            self.servicelist = None

        # Widgeti
        self["mini_picon"]     = Pixmap()
        self["channel_name"]  = Label("")
        self["mini_snr_label"] = Label("SNR")
        self["mini_snr_bar"]   = ProgressBar()
        self["snr_value"]      = Label("")
        self["snr_db"]    = Label("")
        self["mini_agc_label"] = Label("AGC")
        self["mini_agc_bar"]   = ProgressBar()
        self["agc_value"]      = Label("")
        self["mini_line1"]     = Label("")
        self["mini_line2"]     = Label("")
        self["mini_line3"]     = Label("")

        # PiconManager
        self.picon_manager = None
        if HAS_PICON_MANAGER:
            try:
                self.picon_manager = PiconManager("/picon/")
            except Exception as e:
                print(f"[CiefpSignalInfoMini] PiconManager init error: {e}")

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.close,
                "cancel": self.close,
                "red": self.close,
                "blue": self.close,
                # Navigacija kanala
                "left": self.channelDown,
                "right": self.channelUp,
                "up": self.openChannelList,
                "down": self.openChannelList,
            },
            -2
        )

        # Auto-close timer (10 sekundi, resetuje se pri promeni kanala)
        self.auto_close_timer = eTimer()
        self.auto_close_timer.callback.append(self.close)
        self.auto_close_timer.start(15000, True)  # True = jednokratno

        self["channel_name"].setText(self.getChannelNameShort())
        # === Pretplata na promenu kanala ===
        self.nav_event_callback = None
        try:
            self.nav_event_callback = self.session.nav.event.append
            self.nav_event_callback(self.onNavEvent)
            print("[CiefpSignalInfoMini] Subscribed to nav events")
        except Exception as e:
            print(f"[CiefpSignalInfoMini] nav.event subscribe error: {e}")

        # Prvo osvežavanje
        self.onLayoutFinish.append(self.updateMiniInfo)

        # Otkači se pri zatvaranju
        self.onClose.append(self.cleanup)

    # ---------------- CLEANUP ----------------
    def cleanup(self):
        try:
            if self.nav_event_callback is not None:
                self.session.nav.event.remove(self.onNavEvent)
                print("[CiefpSignalInfoMini] Unsubscribed from nav events")
        except Exception as e:
            print(f"[CiefpSignalInfoMini] cleanup error: {e}")

        # Očisti pending timere
        try:
            if hasattr(self, "_pending_timers"):
                for t in self._pending_timers:
                    try:
                        t.stop()
                    except:
                        pass
                self._pending_timers = []
        except:
            pass

        try:
            if self.servicelist:
                self.servicelist.close()
                self.servicelist = None
        except Exception as e:
            print(f"[CiefpSignalInfoMini] servicelist close error: {e}")

        try:
            if self.auto_close_timer:
                self.auto_close_timer.stop()
        except:
            pass
    # ---------------- NAV EVENT ----------------
    def onNavEvent(self, event):
        """Callback na promenu servisa."""
        # event == 1 znači "service started"
        if event == 1:
            print("[CiefpSignalInfoMini] Service changed, refreshing...")
            # Dodaj kratku pauzu da se signal stabilizuje
            self.refresh_timer = eTimer()
            self.refresh_timer.callback.append(self._doRefresh)
            self.refresh_timer.start(300, True)  # 300ms delay
            # Resetuj auto-close timer
            try:
                self.auto_close_timer.start(15000, True)
            except:
                pass

    def _doRefresh(self):
        """Stvarno osvežavanje nakon kratke pauze."""
        try:
            self.updateMiniInfo()
        except Exception as e:
            print(f"[CiefpSignalInfoMini] _doRefresh error: {e}")

    # ---------------- CHANNEL NAVIGATION ----------------
    def openChannelList(self):
        if self.servicelist:
            self.session.execDialog(self.servicelist)
    def channelUp(self):
        """Prebaci na sledeći kanal."""
        try:
            if self.servicelist:
                self.servicelist.moveDown()
                self.servicelist.zap()
                print("[CiefpSignalInfoMini] Channel UP")
                # Osveži odmah + sa malim odlaganjem
                self._scheduleRefresh()
        except Exception as e:
            print(f"[CiefpSignalInfoMini] channelUp error: {e}")

    def channelDown(self):
        """Prebaci na prethodni kanal."""
        try:
            if self.servicelist:
                self.servicelist.moveUp()
                self.servicelist.zap()
                print("[CiefpSignalInfoMini] Channel DOWN")
                self._scheduleRefresh()
        except Exception as e:
            print(f"[CiefpSignalInfoMini] channelDown error: {e}")

    def _scheduleRefresh(self):
        """Zakaži osvežavanje nakon kratke pauze."""
        # Sačuvaj reference da ih možemo očistiti
        if not hasattr(self, "_pending_timers"):
            self._pending_timers = []

        # Prvo osvežavanje - odmah
        self.updateMiniInfo()

        # Dodatna osvežavanja
        for delay in (300, 800):
            t = eTimer()
            t.callback.append(self.updateMiniInfo)
            t.start(delay, True)
            self._pending_timers.append(t)

    # ---------------- Channel Name ----------------
    def getChannelNameShort(self):
        service = self.session.nav.getCurrentService()
        if service:
            info = service.info()
            if info:
                name = info.getName() or ""
                return name[:30]
        return ""

    # ---------------- GLAVNI UPDATE ----------------
    def updateMiniInfo(self):
        try:
            # Picon
            self.updateMiniPicon()

            # === NOVO: Osveži ime kanala ===
            self["channel_name"].setText(self.getChannelNameShort())

            # Signal bars
            snr_db, snr_percent, ber, agc, is_crypted, sid, tsid, onid = self.getSignalFromFrontend()
            snr_val = int(max(0, min(100, snr_percent)))
            agc_val = int(max(0, min(100, agc)))
            self["mini_snr_bar"].setValue(snr_val)
            self["mini_agc_bar"].setValue(agc_val)

            # Parametri (3 linije)
            l1, l2, l3 = self.getMiniParams()
            self["mini_line1"].setText(l1)
            self["mini_line2"].setText(l2)
            self["mini_line3"].setText(l3)

            self["snr_value"].setText(f"{snr_val}%")
            self["agc_value"].setText(f"{agc_val}%")

            if snr_db <= 0.0 and snr_val > 0:
                approx_db = (snr_val / 100.0) * 20.0
                self["snr_db"].setText(f"DB:{approx_db:.2f}")
            else:
                self["snr_db"].setText(f"DB:{snr_db:.2f}")

        except Exception as e:
            print(f"[CiefpSignalInfoMini] updateMiniInfo error: {e}")

    # ---------------- PARAMETRI ----------------
    def getMiniParams(self):
        """Vraća 3 linije parametara zavisno od tunera."""
        service = self.session.nav.getCurrentService()
        if not service:
            return ("N/A", "N/A", "N/A")

        frontendInfo = service.frontendInfo()
        if not frontendInfo:
            return ("N/A", "N/A", "N/A")

        fd = frontendInfo.getAll(True)
        if not fd:
            return ("N/A", "N/A", "N/A")

        tuner_type = fd.get("tuner_type", "") or ""

        # === DVB-S ===
        if tuner_type == "DVB-S":
            freq = fd.get("frequency", 0) // 1000
            pol = self.getPolarization(fd.get("polarization", 0))
            sr = fd.get("symbol_rate", 0) // 1000
            fec = self.getFecShort(fd.get("fec_inner", 0))
            system = self.getSystemShort(tuner_type, fd.get("system", 0))
            mod = self.getModulationShort(fd.get("modulation", 0))

            return (
                f"{freq}  {pol}",
                f"{sr}  {fec}",
                f"{system}  {mod}"
            )
        # === DVB-T / T2 ===
        elif tuner_type in ("DVB-T", "DVB-T2"):
            freq_hz = fd.get("frequency", 0)
            freq_mhz = freq_hz // 1000000  # MHz

            # === DVB-T kanal iz frekvencije (UHF opseg 21-69) ===
            channel_num = None
            if 470 <= freq_mhz <= 862:
                try:
                    channel_num = (freq_mhz - 306) // 8
                except:
                    channel_num = None

            cr_hp = self.getFecShort(fd.get("code_rate_hp", 0))
            const = self.getConstellationShort(fd.get("constellation", 0))
            system = self.getSystemShort(tuner_type, fd.get("system", 0))
            mode = self.getTransmissionModeShort(fd.get("transmission_mode", 0))

            # Prva linija: CH:24  498MHz  (ili bez CH ako nije UHF)
            if channel_num is not None:
                line1 = f"CH:{channel_num}  {freq_mhz}MHz"
            else:
                line1 = f"{freq_mhz}MHz"

            return (
                line1,
                f"{cr_hp}  {const}",
                f"{system}  {mode}"
            )

        # === DVB-C / C2 ===
        elif tuner_type in ("DVB-C", "DVB-C2"):
            freq_mhz = fd.get("frequency", 0) // 1000000
            sr = fd.get("symbol_rate", 0) // 1000
            mod = self.getModulationShort(fd.get("modulation", 0))
            fec = self.getFecShort(fd.get("fec_inner", 0))
            system = self.getSystemShort(tuner_type, fd.get("system", 0))

            return (
                f"{freq_mhz} MHz",
                f"{sr}  {mod}",
                f"{system}  {fec}"
            )

        else:
            freq = fd.get("frequency", 0) // 1000
            return (
                f"{freq}",
                tuner_type or "N/A",
                "N/A"
            )

    # ---------------- SIGNAL ----------------
    def getSignalFromFrontend(self):
        service = self.session.nav.getCurrentService()
        if not service:
            return 0.0, 0, 0, 0, 0, 0, 0, 0

        frontendInfo = service.frontendInfo()
        if not frontendInfo:
            return 0.0, 0, 0, 0, 0, 0, 0, 0

        try:
            fd = frontendInfo.getAll(True)
            quality = fd.get("tuner_signal_quality", 0)
            snr_percent = min(100, quality // 655)
            snr_db = fd.get("tuner_signal_quality_db", 0) / 100.0
            ber = fd.get("tuner_bit_error_rate", 0)
            agc = min(100, fd.get("tuner_signal_power", 0) // 655)

            info = service.info()
            is_crypted = info.getInfo(iServiceInformation.sIsCrypted)
            sid  = info.getInfo(iServiceInformation.sSID)
            tsid = info.getInfo(iServiceInformation.sTSID)
            onid = info.getInfo(iServiceInformation.sONID)

            return snr_db, snr_percent, ber, agc, is_crypted, sid, tsid, onid
        except Exception as e:
            print(f"[CiefpSignalInfoMini] getSignalFromFrontend error: {e}")
            return 0.0, 0, 0, 0, 0, 0, 0, 0

    # ---------------- PICON ----------------
    def updateMiniPicon(self):
        """Učitaj picon za trenutni kanal."""
        try:
            service_ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if not service_ref:
                self.loadMiniPlaceholder()
                return

            ref_str = service_ref.toString()

            channel_name = ""
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    channel_name = info.getName() or ""

            # PiconManager
            if self.picon_manager:
                try:
                    pix = self.picon_manager.get_picon_pixmap(ref_str, channel_name)
                    if pix:
                        self["mini_picon"].instance.setPixmap(pix)
                        return
                except Exception as e:
                    print(f"[CiefpSignalInfoMini] PiconManager error: {e}")

            # Fallback
            variants = self._generatePiconVariants(ref_str)
            search_paths = [
                "/picon/",
                "/media/hdd/picon/",
                "/media/usb/picon/",
                "/media/card/picon/",
                "/etc/enigma2/picon/",
                "/usr/share/enigma2/picon/",
            ]
            for variant in variants:
                for base in search_paths:
                    picon_path = os.path.join(base, variant)
                    if fileExists(picon_path):
                        pix = LoadPixmap(picon_path)
                        if pix:
                            self["mini_picon"].instance.setPixmap(pix)
                            return

            self.loadMiniPlaceholder()
        except Exception as e:
            print(f"[CiefpSignalInfoMini] updateMiniPicon error: {e}")
            self.loadMiniPlaceholder()

    def loadMiniPlaceholder(self):
        try:
            placeholder = f"{PLUGIN_PATH}/placeholder.png"
            if fileExists(placeholder):
                pix = LoadPixmap(placeholder)
                if pix:
                    self["mini_picon"].instance.setPixmap(pix)
                    return
            self["mini_picon"].instance.setPixmap(None)
        except Exception as e:
            print(f"[CiefpSignalInfoMini] loadMiniPlaceholder error: {e}")

    def _generatePiconVariants(self, ref_str):
        variants = []
        try:
            ref_str = ref_str.strip()
            while ref_str.endswith(':'):
                ref_str = ref_str[:-1]

            parts = ref_str.split(":")
            while parts and parts[-1] == "":
                parts.pop()

            variants.append("_".join(parts) + ".png")
            if len(parts) > 3:
                variants.append("_".join(parts[:-3]) + ".png")
            if len(parts) >= 7:
                variants.append("_".join(parts[:7]) + ".png")
            if len(parts) >= 6:
                variants.append("_".join(parts[3:6]) + ".png")

            seen = set()
            unique = []
            for v in variants:
                if v and v not in seen:
                    seen.add(v)
                    unique.append(v)
            return unique
        except:
            return variants

    # ---------------- POMOĆNE ----------------
    def getPolarization(self, pol):
        return {0: "H", 1: "V", 2: "L", 3: "R"}.get(pol, "?")

    def getFecShort(self, fec):
        return {0: "Auto", 1: "1/2", 2: "2/3", 3: "3/4", 4: "5/6",
                5: "7/8", 6: "8/9", 7: "3/5", 8: "4/5", 9: "9/10"}.get(fec, "?")

    def getModulationShort(self, mod):
        return {0: "Auto", 1: "QPSK", 2: "8PSK", 3: "64QAM",
                4: "16APSK", 5: "32APSK"}.get(mod, "?")

    def getSystemShort(self, tuner_type, sys):
        if tuner_type == "DVB-S":
            return {0: "DVB-S", 1: "DVB-S2", 2: "DVB-S2X"}.get(sys, "?")
        elif tuner_type == "DVB-T":
            return {0: "DVB-T", 1: "DVB-T2"}.get(sys, "?")
        elif tuner_type == "DVB-C":
            return {0: "DVB-C", 1: "DVB-C2"}.get(sys, "?")
        return "?"

    def getConstellationShort(self, const):
        return {0: "Auto", 1: "QPSK", 2: "16QAM", 3: "64QAM", 4: "256QAM"}.get(const, "?")

    def getTransmissionModeShort(self, mode):
        return {0: "Auto", 1: "2K", 2: "8K", 3: "4K",
                4: "1K", 5: "16K", 6: "32K"}.get(mode, "?")