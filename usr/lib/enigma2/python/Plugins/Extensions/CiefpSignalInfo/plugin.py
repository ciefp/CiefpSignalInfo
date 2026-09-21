from Plugins.Plugin import PluginDescriptor

def main(session, **kwargs):
    from .CiefpSignalInfo import CiefpSignalInfoScreen
    session.open(CiefpSignalInfoScreen)

def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Ciefp Signal Info 1.7",
            description="Signal and channel information",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="icon_plugin.png",
            fnc=main
        )
    ]