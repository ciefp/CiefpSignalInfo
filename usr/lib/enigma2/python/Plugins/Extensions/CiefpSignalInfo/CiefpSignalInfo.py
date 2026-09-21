from enigma import iServiceInformation, eTimer
from Screens.Screen import Screen
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.ActionMap import ActionMap
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS  # ← DODATO
import os
from Screens.MessageBox import MessageBox
from .CiefpSignalInfoMini import CiefpSignalInfoMini

# ==== UVOZ LOKALNOG PiconManager ====
try:
    from .components.picon_manager import PiconManager
    HAS_PICON_MANAGER = True
    print("[CiefpSignalInfo] Local PiconManager imported OK")
except ImportError as e:
    HAS_PICON_MANAGER = False
    print(f"[CiefpSignalInfo] Local PiconManager NOT available: {e}")

VERSION = "1.7"
PLUGIN_PATH = "/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo"

# ==== Satfinder putanje ====
Satfinderpy  = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/Satfinder/plugin.py")
Satfinderpyc = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/Satfinder/plugin.pyc")
Satfinderpyo = resolveFilename(SCOPE_PLUGINS, "SystemPlugins/Satfinder/plugin.pyo")

class CiefpSignalInfoScreen(Screen):
    skin = """
    <screen name="CiefpSignalInfoScreen" position="center,center" size="1920,1080"
             backgroundColor="#0D1B36">

        <widget name="separator0" position="0,5" size="1920,3" backgroundColor="#d5fa02" zPosition="1" />
        <widget name="plugin_title" position="0,10" size="1920,60" font="Bold;40" halign="center" backgroundColor="#012e01" foregroundColor="#FFFFFF" text="..:: Ciefp Signal Info ::.." />
        <widget name="separator1" position="0,70" size="1920,3" backgroundColor="#d5fa02" zPosition="1" />

        <widget source="Title" render="Label" position="0,20" size="1520,70"
                font="Regular;52" halign="center" valign="center"
                foregroundColor="#FFFFFF" transparent="1" />
        <widget name="separator3" position="1550,70" size="3,750" backgroundColor="#d5fa02" zPosition="1" />
        <widget name="time_label" position="1600,75" size="320,50"
                font="Regular;46" halign="center" valign="center"
                foregroundColor="#FFFFFF" transparent="1" />
        <widget name="date_label" position="1600,130" size="320,50"
                font="Regular;46" halign="center" valign="center"
                foregroundColor="#FFFFFF" transparent="1" />

        <eLabel position="40,150" size="1420,790"
                backgroundColor="#0D1B36" foregroundColor="#00FF00"
                borderWidth="3" borderColor="#00C000" zPosition="-1" />

        <widget name="info_left" position="70,180" size="680,740"
                font="Console;26" transparent="1" foregroundColor="#FFFFFF"
                halign="left" valign="top" />

        <widget name="info_right" position="790,180" size="650,740"
                font="Console;26" transparent="1" foregroundColor="#FFFFFF"
                halign="left" valign="top" />

        <widget name="channel_picon" position="1650,200" size="220,132"
                 alphatest="blend" transparent="1" />

        <widget name="channel_name" position="1600,320" size="320,80"
                font="Bold;36" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />

        <widget name="plugin_logo" position="1600,400" size="300,200"
                pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo/plugin_logo.png"
                alphatest="blend" transparent="1" />
        <widget name="separator4" position="0,820" size="1920,3" backgroundColor="#d5fa02" zPosition="1" />
         <!-- === ECM STATUS TRAKA === -->
        <widget name="ecm_status" position="50,830" size="1850,40"
                font="Console;24" halign="left" valign="center"
                foregroundColor="#00FF00" backgroundColor="#0D1B36"
                transparent="1" />
        <widget name="satellite_name" position="50,880" size="520,40"
                font="Console;24" halign="left" valign="center"
                foregroundColor="#00FF00" transparent="1" />
        <widget name="separator2" position="0,920" size="1920,3" backgroundColor="#d5fa02" zPosition="1" />
        <widget name="key_red" position="1600,610" size="300,40" 
                backgroundColor="red" font="Bold;24" foregroundColor="#000000"  halign="center" valign="center" />
        <widget name="key_green" position="1600,660" size="300,40" 
                backgroundColor="green" font="Bold;24" foregroundColor="#000000"  halign="center" valign="center" />
        <widget name="key_yellow" position="1600,710" size="300,40" 
                backgroundColor="yellow" font="Bold;24" foregroundColor="#000000"  halign="center" valign="center" /> 
        <widget name="key_blue" position="1600,760" size="300,40" 
                backgroundColor="blue" font="Bold;24" foregroundColor="#000000"  halign="center" valign="center" /> 
        
        <widget name="snr_label" position="40,940" size="120,50"
                font="Bold;36" halign="left" valign="center"
                foregroundColor="#FFD700" transparent="1" />
        <widget name="snr_bar" position="180,940" size="1180,40"
                pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo/icon_snr.png"
                borderWidth="2" borderColor="#000000" />
        <widget name="snr_value" position="1380,940" size="180,50"
                font="Bold;46" halign="center" valign="center"
                foregroundColor="#FFD700" transparent="1" />
        <widget name="snr_db" position="1560,940" size="340,50"
                font="Bold;46" halign="center" valign="center"
                foregroundColor="#00FF00" transparent="1" />

        <widget name="agc_label" position="40,990" size="120,50"
                font="Bold;44" halign="left" valign="center"
                foregroundColor="#FFD700" transparent="1" />
        <widget name="agc_bar" position="180,990" size="1180,40"
                pixmap="/usr/lib/enigma2/python/Plugins/Extensions/CiefpSignalInfo/icon_agc.png"
                borderWidth="2" borderColor="#000000" />
        <widget name="agc_value" position="1380,990" size="180,50"
                font="Bold;46" halign="center" valign="center"
                foregroundColor="#FFD700" transparent="1" />
    </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)

        self["time_label"]   = Label("")
        self["date_label"]   = Label("")
        self["info_left"]    = Label("")
        self["info_right"]   = Label("")

        self["plugin_title"] = Label("..:: Ciefp Signal Info ::..")
        self["ecm_status"] = Label("")
        self["key_red"] = Label("EXIT")
        self["key_blue"] = Label("MINI SKIN")
        self["key_yellow"] = Label("PLACEHOLDER")
        self["key_green"] = Label("SATFINDER")

        self["channel_picon"] = Pixmap()
        self["channel_name"]  = Label("")
        self["ca_info"]       = Label("")
        self["satellite_name"] = Label("")
        self["plugin_logo"]   = Pixmap()

        self["snr_label"] = Label("SNR")
        self["snr_bar"]   = ProgressBar()
        self["snr_value"] = Label("")
        self["snr_db"]    = Label("")

        self["agc_label"] = Label("AGC")
        self["agc_bar"]   = ProgressBar()
        self["agc_value"] = Label("")

        self["separator0"] = Label()
        self["separator1"] = Label()
        self["separator2"] = Label()
        self["separator3"] = Label()
        self["separator4"] = Label()

        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions"],
            {
                "ok": self.close,
                "cancel": self.close,
                "red": self.close,
                "green": self.openSatfinder,   # ← NOVO
                "yellow": self.close,
                "blue": self.openMiniInfo,
            },
            -2
        )

        # === KLJUČNO: Instanciraj ChannelSelection da drži tuner aktivnim ===
        self.servicelist = None
        try:
            from Screens.ChannelSelection import ChannelSelection
            self.servicelist = self.session.instantiateDialog(ChannelSelection)
            print("[CiefpSignalInfo] ChannelSelection instantiated")
        except Exception as e:
            print(f"[CiefpSignalInfo] ChannelSelection init error: {e}")

        # ==== Inicijalizuj LOKALNI PiconManager ====
        self.picon_manager = None
        if HAS_PICON_MANAGER:
            try:
                self.picon_manager = PiconManager("/picon/")
                print("[CiefpSignalInfo] Local PiconManager initialized OK")
            except Exception as e:
                print(f"[CiefpSignalInfo] PiconManager init error: {e}")
                self.picon_manager = None

        # Timer za vreme
        self.time_timer = eTimer()
        self.time_timer.callback.append(self.updateTime)
        self.time_timer.start(1000)
        self.onClose.append(self.time_timer.stop)

        # Timer za signal / info
        self.signal_timer = eTimer()
        self.signal_timer.callback.append(self.updateAllInfo)
        self.signal_timer.start(1000)
        self.onClose.append(self.signal_timer.stop)

        self.onLayoutFinish.append(self.updateAllInfo)

    # ---------------- VREME ----------------
    def updateTime(self):
        import time
        try:
            self["time_label"].setText(time.strftime("%H:%M"))
            self["date_label"].setText(time.strftime("%d.%m.%Y"))
        except:
            pass

    # ---------------- GLAVNI UPDATE ----------------
    def updateAllInfo(self):
        try:
            self["info_left"].setText(self.getLeftInfo())
            self["info_right"].setText(self.getRightInfo())

            snr_db, snr_percent, ber, agc, is_crypted, sid, tsid, onid = self.getSignalFromFrontend()
            self.updateSignalBars(snr_percent, snr_db, agc)

            self["channel_name"].setText(self.getChannelNameShort())
            self["ca_info"].setText(self.getCAInfoShort())
            self["satellite_name"].setText(self.getSatelliteNameShort())

            # === NOVO: ECM Status ===
            self["ecm_status"].setText(self.getECMStatusText())

            self.updatePicon()
        except Exception as e:
            print("[CiefpSignalInfo] updateAllInfo error:", e)
    # ---------------- SIGNAL BARS ----------------
    def updateSignalBars(self, snr_percent, snr_db, agc):
        try:
            snr_val = int(max(0, min(100, snr_percent)))
            agc_val = int(max(0, min(100, agc)))
            self["snr_bar"].setValue(snr_val)
            self["agc_bar"].setValue(agc_val)
            self["snr_value"].setText(f"{snr_val}%")
            self["agc_value"].setText(f"{agc_val}%")

            if snr_db <= 0.0 and snr_val > 0:
                approx_db = (snr_val / 100.0) * 20.0
                self["snr_db"].setText(f"DB:{approx_db:.2f}")
            else:
                self["snr_db"].setText(f"DB:{snr_db:.2f}")
        except Exception as e:
            print("[CiefpSignalInfo] updateSignalBars error:", e)

    # ---------------- FRONTEND ----------------
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
            print("[CiefpSignalInfo] getSignalFromFrontend error:", e)
            return 0.0, 0, 0, 0, 0, 0, 0, 0

    # ---------------- LEVA STRANA ----------------
    def getLeftInfo(self):
        service = self.session.nav.getCurrentService()
        if not service:
            return "❌ Nema aktivnog servisa."
        info = service.info()
        if not info:
            return "❌ Ne mogu dohvatiti info objekat."
        frontendInfo = service.frontendInfo()
        fd = frontendInfo and frontendInfo.getAll(True)
        if not fd:
            return "❌ Ne mogu dohvatiti frontend podatke."

        tuner_type = fd.get("tuner_type", "") or ""

        try:
            name = info.getName() or "N/A"
        except:
            name = "N/A"

        try:
            provider = info.getInfoString(iServiceInformation.sProvider) or "N/A"
        except:
            provider = "N/A"

        try:
            vpid = info.getInfo(iServiceInformation.sVideoPID)
            vpid_str = f"0x{vpid:X}" if vpid != -1 else "N/A"
        except:
            vpid_str = "N/A"

        try:
            apid = info.getInfo(iServiceInformation.sAudioPID)
            apid_str = f"0x{apid:X}" if apid != -1 else "N/A"
        except:
            apid_str = "N/A"

        try:
            pcr = info.getInfo(iServiceInformation.sPCRPID)
            pcr_str = f"0x{pcr:X}" if pcr != -1 else "N/A"
        except:
            pcr_str = "N/A"

        try:
            pmt = info.getInfo(iServiceInformation.sPMTPID)
            pmt_str = f"0x{pmt:X}" if pmt != -1 else "N/A"
        except:
            pmt_str = "N/A"

        try:
            txt = info.getInfo(iServiceInformation.sTXTPID)
            txt_str = f"0x{txt:X}" if txt != -1 else "N/A"
        except:
            txt_str = "N/A"

        text = (
            f"Channel:      {name}\n"
            f"Provider:     {provider}\n"
        )

        if tuner_type == "DVB-S":
            try:
                orbital_pos = fd.get("orbital_position", 0)
                sat_name = self.getSatelliteNameFromXML(orbital_pos)
            except:
                sat_name = "N/A"

            try:
                freq = fd.get("frequency", 0) // 1000
            except:
                freq = 0

            try:
                pol_str = self.getPolarization(fd.get("polarization", 0))
            except:
                pol_str = "N/A"

            try:
                sr = fd.get("symbol_rate", 0) // 1000
            except:
                sr = 0

            try:
                fec_str = self.getFec(fd.get("fec_inner", 0))
            except:
                fec_str = "N/A"

            try:
                mod_str = self.getModulation(fd.get("modulation", 0))
            except:
                mod_str = "N/A"

            try:
                system_str = self.getSystem(tuner_type, fd.get("system", 0))
            except:
                system_str = "N/A"

            try:
                pls_mode = fd.get("pls_mode", -1)
                pls_mode_str = {0: "Root", 1: "Gold", 2: "Combo"}.get(pls_mode, "N/A")
            except:
                pls_mode_str = "N/A"

            try:
                pls_code = fd.get("pls_code", -1)
                pls_code_str = str(pls_code) if pls_code >= 0 else "N/A"
            except:
                pls_code_str = "N/A"

            text += (
                f"Satellite:    {sat_name}\n"
                f"Frequency:    {freq} MHz\n"
                f"Polarization: {pol_str}\n"
                f"Symbol Rate:  {sr} kSym/s\n"
                f"FEC:          {fec_str}\n"
                f"Modulation:   {mod_str}\n"
                f"System:       {system_str}\n"
                f"PLS MODE:     {pls_mode_str}\n"
                f"PLS CODE:     {pls_code_str}\n"
            )
        elif tuner_type in ("DVB-T", "DVB-T2"):
            try:
                system_str = self.getSystem(tuner_type, fd.get("system", 0))
            except:
                system_str = "N/A"

            try:
                freq_hz = fd.get("frequency", 0)
                freq = freq_hz // 1000  # kHz
            except:
                freq_hz = 0
                freq = 0

            # === NOVO: DVB-T kanal iz frekvencije ===
            try:
                freq_mhz = freq_hz // 1000000
                if 470 <= freq_mhz <= 862:
                    channel_num = (freq_mhz - 306) // 8
                    channel_str = f"Channel:      {channel_num}\n"
                else:
                    channel_str = "Channel:      N/A\n"
            except:
                channel_str = ""

            try:
                bw_str = self.getBandwidth(fd.get("bandwidth", 0))
            except:
                bw_str = "N/A"
            try:
                cr_hp_str = self.getFec(fd.get("code_rate_hp", 0))
            except:
                cr_hp_str = "N/A"

            try:
                cr_lp_str = self.getFec(fd.get("code_rate_lp", 0))
            except:
                cr_lp_str = "N/A"

            try:
                constellation_str = self.getConstellation(fd.get("constellation", 0))
            except:
                constellation_str = "N/A"

            try:
                transmission_mode_str = self.getTransmissionMode(fd.get("transmission_mode", 0))
            except:
                transmission_mode_str = "N/A"

            try:
                guard_interval_str = self.getGuardInterval(fd.get("guard_interval", 0))
            except:
                guard_interval_str = "N/A"

            try:
                hierarchy_str = self.getHierarchy(fd.get("hierarchy_information", 0))
            except:
                hierarchy_str = "N/A"

            text += (
                f"{channel_str}"
                f"Frequency:    {freq} MHz\n"
                f"System:       {system_str}\n"
                f"Bandwidth:    {bw_str}\n"
                f"Code Rate HP: {cr_hp_str}\n"
                f"Code Rate LP: {cr_lp_str}\n"
                f"Constellation:{constellation_str}\n"
                f"Trans. Mode:  {transmission_mode_str}\n"
                f"Guard Int.:   {guard_interval_str}\n"
                f"Hierarchy:    {hierarchy_str}\n"
            )

        elif tuner_type in ("DVB-C", "DVB-C2"):
            try:
                system_str = self.getSystem(tuner_type, fd.get("system", 0))
            except:
                system_str = "N/A"

            try:
                freq = fd.get("frequency", 0) // 1000
            except:
                freq = 0

            try:
                sr = fd.get("symbol_rate", 0) // 1000
            except:
                sr = 0

            try:
                mod_str = self.getModulation(fd.get("modulation", 0))
            except:
                mod_str = "N/A"

            try:
                fec_str = self.getFec(fd.get("fec_inner", 0))
            except:
                fec_str = "N/A"

            text += (
                f"Frequency:    {freq} MHz\n"
                f"Symbol Rate:  {sr} kSym/s\n"
                f"Modulation:   {mod_str}\n"
                f"FEC:          {fec_str}\n"
                f"System:       {system_str}\n"
            )

        else:
            try:
                freq = fd.get("frequency", 0) // 1000
            except:
                freq = 0
            text += (
                f"Frequency:    {freq} MHz\n"
                f"System:       {tuner_type or 'N/A'}\n"
            )

        text += (
            f"\n"
            f"Video PID:    {vpid_str}\n"
            f"Audio PID:    {apid_str}\n"
            f"PCR PID:      {pcr_str}\n"
            f"PMT PID:      {pmt_str}\n"
            f"Teletext PID: {txt_str}"
        )

        return text

    # ---------------- DESNA STRANA ----------------
    def getRightInfo(self):
        service = self.session.nav.getCurrentService()
        if not service:
            return ""
        info = service.info()
        if not info:
            return ""

        service_ref = self.getServiceReference()

        try:
            caids = info.getInfoObject(iServiceInformation.sCAIDs) or []
        except:
            caids = []

        active_caid = None
        ecm_path = "/tmp/ecm.info"
        if os.path.exists(ecm_path):
            try:
                with open(ecm_path, "r") as f:
                    for line in f:
                        if line.startswith("caid:"):
                            caid_str = line.split(":")[1].strip().replace("0x", "")
                            try:
                                active_caid = int(caid_str, 16)
                                break
                            except:
                                pass
            except:
                pass

        caid_lines = []
        if caids:
            for caid in sorted(set(caids)):
                name = self.getCaName(caid)
                marker = "  [ACTIVE]" if caid == active_caid else ""
                if name:
                    caid_lines.append(f"  {name} (0x{caid:04X}){marker}")
                else:
                    caid_lines.append(f"  CAID 0x{caid:04X}{marker}")
        else:
            caid_lines.append("  No encryption")

        try:
            sid  = info.getInfo(iServiceInformation.sSID)
            tsid = info.getInfo(iServiceInformation.sTSID)
            onid = info.getInfo(iServiceInformation.sONID)
        except:
            sid = tsid = onid = -1

        lines = []
        lines.append("Encryption:")
        lines.extend(caid_lines)
        lines.append("")
        lines.append("SI / TS / ONID:")
        lines.append(f"  SID:  0x{sid:04X}")
        lines.append(f"  TSID: 0x{tsid:04X}")
        lines.append(f"  ONID: 0x{onid:04X}")
        lines.append("")
        lines.append("Service Reference:")
        lines.append(f"  {service_ref}")
        return "\n".join(lines)

    # ---------------- DESNA STRANA - KRATKO ----------------
    def getChannelNameShort(self):
        service = self.session.nav.getCurrentService()
        if service:
            info = service.info()
            if info:
                name = info.getName() or ""
                return name[:30]
        return ""

    def getCAInfoShort(self):
        service = self.session.nav.getCurrentService()
        if service:
            info = service.info()
            if info:
                caids = info.getInfoObject(iServiceInformation.sCAIDs) or []
                if caids:
                    name = self.getCaName(caids[0])
                    if name:
                        return f"{name.upper()} (0x{caids[0]:04X})"
        return ""

    def getSatelliteNameShort(self):
        service = self.session.nav.getCurrentService()
        if not service:
            return ""
        frontendInfo = service.frontendInfo()
        if not frontendInfo:
            return ""
        try:
            fd = frontendInfo.getAll(True)
            if not fd:
                return ""
            tuner_type = fd.get("tuner_type", "") or ""
            if tuner_type != "DVB-S":
                return ""
            orbital_pos = fd.get("orbital_position", 0)
            return self.getSatelliteNameFromXML(orbital_pos)
        except:
            return ""

    # ---------------- PICON ----------------
    def loadPlaceholder(self):
        """Učitaj placeholder.png ako picon ne postoji."""
        try:
            placeholder = f"{PLUGIN_PATH}/placeholder.png"
            if fileExists(placeholder):
                pix = LoadPixmap(placeholder)
                if pix:
                    self["channel_picon"].instance.setPixmap(pix)
                    return
            self["channel_picon"].instance.setPixmap(None)
        except Exception as e:
            print("[CiefpSignalInfo] loadPlaceholder error:", e)

    def updatePicon(self):
        """Učitaj picon - koristi LOKALNI PiconManager."""
        try:
            service_ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if not service_ref:
                self.loadPlaceholder()
                return

            ref_str = service_ref.toString()

            # Uzmi ime kanala za fallback
            channel_name = ""
            service = self.session.nav.getCurrentService()
            if service:
                info = service.info()
                if info:
                    channel_name = info.getName() or ""

            # === METODA 1: Lokalni PiconManager ===
            if self.picon_manager:
                try:
                    pix = self.picon_manager.get_picon_pixmap(ref_str, channel_name)
                    if pix:
                        self["channel_picon"].instance.setPixmap(pix)
                        return
                except Exception as e:
                    print(f"[CiefpSignalInfo] PiconManager error: {e}")

            # === METODA 2: Fallback ===
            variants = self._generate_picon_variants(ref_str)
            search_paths = [
                "/picon/",
                "/media/hdd/picon/",
                "/media/usb/picon/",
                "/media/card/picon/",
                "/etc/enigma2/picon/",
                "/usr/share/enigma2/picon/",
                f"{PLUGIN_PATH}/picon/",
            ]

            for variant in variants:
                for base in search_paths:
                    picon_path = os.path.join(base, variant)
                    if fileExists(picon_path):
                        pix = LoadPixmap(picon_path)
                        if pix:
                            self["channel_picon"].instance.setPixmap(pix)
                            return

            self.loadPlaceholder()

        except Exception as e:
            print("[CiefpSignalInfo] updatePicon error:", e)
            self.loadPlaceholder()

    def _generate_picon_variants(self, ref_str):
        """Fallback generisanje naziva picona."""
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
            if len(parts) > 4:
                variants.append("_".join(parts[:-4]) + ".png")
            if len(parts) >= 7:
                variants.append("_".join(parts[:7]) + ".png")
                variants.append("_".join(parts[2:7]) + ".png")
            if len(parts) >= 6:
                variants.append("_".join(parts[3:6]) + ".png")
            for extra in range(1, 5):
                variants.append("_".join(parts + ["0"] * extra) + ".png")
            if len(parts) >= 3:
                short = parts[:2] + parts[3:]
                variants.append("_".join(short) + ".png")

            seen = set()
            unique = []
            for v in variants:
                if v and v not in seen:
                    seen.add(v)
                    unique.append(v)
            return unique
        except Exception as e:
            print(f"[CiefpSignalInfo] _generate_picon_variants error: {e}")
            return variants
    # ---------------- ECM INFO ----------------
    def get_ecm_info(self):
        """Parsira /tmp/ecm.info i vraća dict sa podacima.
        Podržava različite formate emulatora (OSCam, NCam, CCcam, mgcamd, itd.)
        """
        ecm_path = "/tmp/ecm.info"
        ecm_data = {
            "system": "N/A",
            "caid": "N/A",
            "provider": "N/A",
            "provid": "N/A",
            "pid": "N/A",
            "chid": "N/A",
            "reader": "N/A",
            "from": "N/A",
            "address": "N/A",
            "using": "N/A",
            "protocol": "N/A",
            "hops": "N/A",
            "ecm_time": "N/A",
            "cw0": "N/A",
            "cw1": "N/A"
        }
        if os.path.exists(ecm_path):
            try:
                with open(ecm_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if ":" not in line:
                            continue
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()

                        # === CA SYSTEM ===
                        if key == "system":
                            ecm_data["system"] = value

                        # === CAID ===
                        elif key == "caid":
                            ecm_data["caid"] = value.replace("0x", "").upper()

                        # === PROVIDER ===
                        elif key == "provider":
                            ecm_data["provider"] = value

                        # === PROVID ===
                        elif key == "provid":
                            ecm_data["provid"] = value.replace("0x", "").upper()

                        # === PID ===
                        elif key == "pid":
                            ecm_data["pid"] = value

                        # === CHID ===
                        elif key in ("chid", "channel"):
                            ecm_data["chid"] = value

                        # === READER ===
                        elif key in ("reader", "source", "src", "card", "cardid"):
                            ecm_data["reader"] = value

                        # === FROM ===
                        elif key in ("from", "host", "ip"):
                            ecm_data["from"] = value

                        # === ADDRESS ===
                        elif key == "address":
                            ecm_data["address"] = value
                            # Ako `from` nije popunjen, koristi address
                            if ecm_data["from"] == "N/A":
                                ecm_data["from"] = value

                        # === USING (protocol) ===
                        elif key == "using":
                            ecm_data["using"] = value
                            # Ako `protocol` nije popunjen, koristi using
                            if ecm_data["protocol"] == "N/A":
                                ecm_data["protocol"] = value

                        # === PROTOCOL ===
                        elif key in ("protocol", "proto"):
                            ecm_data["protocol"] = value

                        # === HOPS ===
                        elif key in ("hops", "hop", "level"):
                            ecm_data["hops"] = value

                        # === ECM TIME ===
                        elif key in ("ecm time", "ecm_time", "time", "ecm"):
                            ecm_data["ecm_time"] = value

                        # === CW ===
                        elif key == "cw0":
                            ecm_data["cw0"] = value
                        elif key == "cw1":
                            ecm_data["cw1"] = value
            except Exception as e:
                print(f"[CiefpSignalInfo] Error reading ecm.info: {str(e)}")
        return ecm_data
    def getECMStatusText(self):
        """Vraća formatiran string za status traku."""
        try:
            ecm = self.get_ecm_info()

            # Ako nema aktivnog ECM-a
            if ecm["caid"] == "N/A" and ecm["hops"] == "N/A":
                return ""

            parts = []

            # Protocol (CCcam, OSCam, itd.)
            if ecm["using"] and ecm["using"] != "N/A":
                parts.append(f"Using: {ecm['using']}")

            # Address (server adresa)
            if ecm["address"] and ecm["address"] != "N/A":
                parts.append(f"Address: {ecm['address']}")

            # Hops
            if ecm["hops"] and ecm["hops"] != "N/A":
                parts.append(f"Hops: {ecm['hops']}")

            # ECM Time
            if ecm["ecm_time"] and ecm["ecm_time"] != "N/A":
                parts.append(f"ECM Time: {ecm['ecm_time']}")

            # CA System + CAID
            if ecm["caid"] and ecm["caid"] != "N/A":
                caid_str = f"CAID: 0x{ecm['caid']}"
                if ecm["system"] and ecm["system"] != "N/A":
                    caid_str = f"{ecm['system']} (0x{ecm['caid']})"
                parts.append(caid_str)

            return "  |  ".join(parts)
        except Exception as e:
            print(f"[CiefpSignalInfo] getECMStatusText error: {e}")
            return ""

    # ---------------- POMOĆNE ----------------
    def getServiceReference(self):
        service = self.session.nav.getCurrentService()
        if service:
            ref = self.session.nav.getCurrentlyPlayingServiceReference()
            if ref:
                return ref.toString()
        return "N/A"

    def getCaName(self, caid):
        known = {
            0x0500: "Viaccess", 0x0600: "Seca", 0x0900: "NDS",
            0x098D: "NDS", 0x098C: "NDS", 0x091F: "NDS", 0x0911: "NDS",
            0x09CD: "NDS", 0x09C4: "NDS", 0x0963: "NDS", 0x0961: "NDS",
            0x0960: "NDS", 0x092B: "NDS", 0x09BD: "NDS", 0x09F0: "NDS",
            0x1813: "Nagravision", 0x1833: "Nagravision", 0x1834: "Nagravision",
            0x1830: "Nagravision", 0x1817: "Nagravision", 0x1818: "Nagravision",
            0x1878: "Nagravision", 0x1819: "Nagravision", 0x1880: "Nagravision",
            0x1883: "Nagravision", 0x1884: "Nagravision", 0x1863: "Nagravision",
            0x183D: "Nagravision", 0x1814: "Nagravision", 0x1810: "Nagravision",
            0x1811: "Nagravision", 0x1802: "Nagravision", 0x1807: "Nagravision",
            0x1843: "Nagravision", 0x1856: "Nagra Ma", 0x183E: "Nagra Ma",
            0x1803: "Nagra Ma", 0x1861: "Nagra Ma", 0x181D: "Nagra Ma",
            0x186C: "Nagra Ma", 0x1870: "Nagra Ma", 0x0E00: "PowerVu",
            0x1700: "Drecrypt", 0x1800: "Tandberg", 0x2600: "Biss",
            0x2700: "Bulcrypt", 0x0D98: "Cryptoworks", 0x0D97: "Cryptoworks",
            0x0D95: "Cryptoworks", 0x0D00: "Cryptoworks", 0x0D01: "Cryptoworks",
            0x0D02: "Cryptoworks", 0x0D03: "Cryptoworks", 0x0D04: "Cryptoworks",
            0x0624: "Irdeto", 0x06E1: "Irdeto", 0x0653: "Irdeto",
            0x0648: "Irdeto", 0x06D9: "Irdeto", 0x0656: "Irdeto",
            0x0650: "Irdeto", 0x0D96: "Irdeto", 0x0629: "Irdeto",
            0x0606: "Irdeto", 0x0664: "Irdeto", 0x06EE: "Irdeto",
            0x06E2: "Irdeto", 0x06F8: "Irdeto", 0x0604: "Irdeto",
            0x069B: "Irdeto", 0x069F: "Irdeto", 0x0B01: "Conax",
            0x0B02: "Conax", 0x0B00: "Conax", 0x4AEE: "Bulcrypt",
            0x5581: "Bulcrypt", 0x1EC0: "CryptoGuard", 0x0100: "Seca",
        }
        return known.get(caid, None)

    def getFec(self, fec):
        return {0: "Auto", 1: "1/2", 2: "2/3", 3: "3/4", 4: "5/6",
                5: "7/8", 6: "8/9", 7: "3/5", 8: "4/5", 9: "9/10"}.get(fec, "N/A")

    def getModulation(self, mod):
        return {0: "Auto", 1: "QPSK", 2: "8PSK", 3: "64QAM",
                4: "16APSK", 5: "32APSK"}.get(mod, "N/A")

    def getSystem(self, tuner_type, sys):
        if tuner_type == "DVB-S":
            return {0: "DVB-S", 1: "DVB-S2", 2: "DVB-S2X"}.get(sys, "N/A")
        elif tuner_type == "DVB-T":
            return {0: "DVB-T", 1: "DVB-T2"}.get(sys, "N/A")
        elif tuner_type == "DVB-C":
            return {0: "DVB-C", 1: "DVB-C2"}.get(sys, "N/A")
        return "N/A"

    def getPolarization(self, pol):
        return {0: "H", 1: "V", 2: "L", 3: "R"}.get(pol, "N/A")

    def getBandwidth(self, bw):
        return {
            0: "Auto",
            6000000: "6 MHz",
            7000000: "7 MHz",
            8000000: "8 MHz",
            10000000: "10 MHz",
        }.get(bw, f"{bw / 1000000:.0f} MHz" if bw else "N/A")

    def getConstellation(self, constellation):
        return {
            0: "Auto",
            1: "QPSK",
            2: "16QAM",
            3: "64QAM",
            4: "256QAM",
        }.get(constellation, "N/A")

    def getTransmissionMode(self, mode):
        return {
            0: "Auto",
            1: "2K",
            2: "8K",
            3: "4K",
            4: "1K",
            5: "16K",
            6: "32K",
        }.get(mode, "N/A")

    def getGuardInterval(self, gi):
        return {
            0: "Auto",
            1: "1/32",
            2: "1/16",
            3: "1/8",
            4: "1/4",
            5: "1/128",
            6: "19/128",
            7: "19/256",
        }.get(gi, "N/A")

    def getHierarchy(self, hi):
        return {
            0: "None",
            1: "1",
            2: "2",
            3: "4",
            4: "Auto",
        }.get(hi, "N/A")

    def getSatelliteNameFromXML(self, orbital_position):
        import xml.etree.ElementTree as ET
        satellites_file = "/etc/tuxbox/satellites.xml"
        if not os.path.exists(satellites_file):
            return self.formatOrbitalPos(orbital_position)
        try:
            tree = ET.parse(satellites_file)
            root = tree.getroot()
            sat_pos = self.convertOrbitalPos(orbital_position)
            for sat in root.findall("sat"):
                pos = int(sat.get("position", "0"))
                if pos == sat_pos:
                    return sat.get("name", self.formatOrbitalPos(orbital_position))
            return self.formatOrbitalPos(orbital_position)
        except:
            return self.formatOrbitalPos(orbital_position)

    def convertOrbitalPos(self, pos):
        return pos - 3600 if pos > 1800 else pos

    def formatOrbitalPos(self, pos):
        pos = self.convertOrbitalPos(pos)
        if pos < 0:
            return f"{abs(pos) / 10.0:.1f}W"
        return f"{pos / 10.0:.1f}E"

    def openMiniInfo(self):
        """Otvori mini signal info (preko glavnog ekrana)."""
        print("[CiefpSignalInfo] Opening mini info")
        self.session.open(CiefpSignalInfoMini, self)

    # ---------------- SATFINDER ----------------
    def openSatfinder(self):
        """Otvori Satfinder - zaustavi svoj timer da ne smeta."""
        print("[CiefpSignalInfo] Opening Satfinder")
        try:
            if not (fileExists(Satfinderpy) or fileExists(Satfinderpyc) or fileExists(Satfinderpyo)):
                self.session.open(
                    MessageBox,
                    _("Satfinder is not installed!"),
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )
                return

            try:
                from Plugins.SystemPlugins.Satfinder.plugin import Satfinder
            except ImportError as e:
                print(f"[CiefpSignalInfo] Satfinder import error: {e}")
                self.session.open(
                    MessageBox,
                    _("Satfinder import failed:\n%s") % str(e),
                    MessageBox.TYPE_ERROR,
                    timeout=5
                )
                return

            # Zaustavi svoj timer da ne smeta Satfinderu
            try:
                self.signal_timer.stop()
                print("[CiefpSignalInfo] signal_timer stopped for Satfinder")
            except Exception as e:
                print(f"[CiefpSignalInfo] signal_timer stop error: {e}")

            # Otvori Satfinder BEZ slot argumenta
            self.session.openWithCallback(self._onSatfinderClosed, Satfinder)

        except Exception as e:
            print(f"[CiefpSignalInfo] openSatfinder error: {e}")

    def _onSatfinderClosed(self, *args):
        """Kada se Satfinder zatvori, pokreni svoj timer ponovo.

        *args - Enigma2 prosleđuje argument (obično None) - ignorišemo ga.
        """
        print(f"[CiefpSignalInfo] Satfinder closed (args={args}), restarting timer")
        try:
            self.signal_timer.start(1000)
            self.updateAllInfo()
        except Exception as e:
            print(f"[CiefpSignalInfo] _onSatfinderClosed error: {e}")