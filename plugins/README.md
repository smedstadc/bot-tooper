#Plugins
##The plugin system is intended as a simple way to extend the bots with custom commands. It has a few simple rules.

- Plugins live in the /plugins directory. Drop your plugin file here and restart the bot. It should load automatically.
- Plugin filenames must be in the form of "*_plugin.py" this is intended to avoid conflicts with python modules in the 
system path.
- Plugins must implement an init_plugin(dict) function. The bot calls this function after loading the plugin and passes
it a reference to the commands dictionary so the plugin can map any number of trigger strings to functions.
- Plugin functions mapped to triggers are expected to return a list of strings. In lieu of no response they should
return an empty list.
- Plugin functions mapped to triggers that expect an argument string must use a keyword to default the value to None.

###The plugin system is a work in progress and may change significantly.
