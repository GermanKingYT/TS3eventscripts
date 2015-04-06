from ts3tools import ts3tools
import json
import time
"""
    This little plugin creates dynamically channel for our official
    kandru teamspeak (ts3.kandru.de). This is great for
    bigger communities with much channels because it deletes
    the unused one and recreates them if neccessary.
"""

# configuration
# configure rooms
config = {}
# config = {'0': {'parent': 2, 'subchan_name': 'Room #[COUNT]', 'channel_properties': {}}, '1': {'parent': 125, 'subchan_name': 'Room #[COUNT]', 'channel_properties': {}},}

# default scan interval (should not be less than 2 seconds)
nextInterval = 2

# plugin name (must be unique!)
name = 'kdr_dynamic_channel'
base = None
core_TS3channel = None

# plugin variables
channellist = {}
nextProof = 0

# initial method (called from ts3eventscripts)
def setup(ts3base):
    global base, core_TS3channel, config, nextInterval
    # get ts3base, it's needed for nearly everything
    base = ts3base
    # get core TS3channel
    core_TS3channel = base.get_class('core.TS3channel')
    # register callbacks
    base.register_callback(name, 'ts3.loop', loop)

    # load config
    config_file = ts3tools.get_instance_config(base, name)
    if config_file is None:
        config_file = ts3tools.get_global_config(name)
    nextInterval = config_file['General']['nextInterval']
    i = 0
    while True:
        room = 'Room_' + str(i)
        if config_file.has_section(room) is True:
            config[i] = {'parent': int(config_file[room]['parent']), 'subchan_name': config_file[room]['subchan_name'], 'channel_properties': json.loads(config_file[room]['channel_properties'])}
        else:
            break
        i = i+1

def loop(self):
    global channellist, core_TS3channel
    channelproof()

def channelproof():
    global config, channellist, core_TS3channel, nextProof
    # if we can proof now or just have to wait
    if nextProof <= time.time():
        # get channel list
        channellist = core_TS3channel.channellist()
        # for each config entry
        for key in config:
            # set counter to 0 (for empty channel)
            numechannel = 0
            # set counter to 0 (for not empty channel)
            numchannel = 0
            # init existing channel dict
            channelexists = {}
            # do we have the parent channel?
            if str(config[key]['parent']) in channellist:
                # go through all channel
                for key2 in channellist:
                    # if we found a subchannel from parent
                    if int(channellist[key2]['pid']) == config[key]['parent']:
                        if '#' in channellist[key2]['channel_name']:
                            channelexists[channellist[key2]['channel_name'].split("#")[1]] = channellist[key2]['cid']
                            # just count them if they are empty
                            if int(channellist[key2]['total_clients']) == 0:
                                numechannel = numechannel + 1
                                # delete them if we got more then one empty channel
                                if numechannel > 1:
                                    core_TS3channel.channeldelete(channellist[key2]['cid'])
                                    numechannel = numechannel - 1
                            else:
                                # count not empty channel
                                numchannel = numchannel + 1
                # if we do not found an empty channel we need to create one :)
                if numechannel == 0:
                    # set channel properties
                    propertiesdict = {'i_channel_needed_join_power': 10, 'channel_codec_quality': 10, 'channel_flag_maxclients_unlimited': 1, 'channel_flag_permanent': 1, 'cpid': config[key]['parent']}
                    propertiesdict.update(config[key]['channel_properties'])
                    # set channel name
                    current = 1
                    channelname = config[key]['subchan_name'].replace('[COUNT]', str(current))
                    # find empty channel ID
                    while 1:
                        # and only proceed if we found an empty channel ID
                        if str(current) not in channelexists.keys():
                            # set channel name to empty ID
                            channelname = config[key]['subchan_name'].replace('[COUNT]', str(current))
                            # if the channel before exist (it must normally exist - or the new channel will be the first channel)
                            if str(current-1) in channelexists.keys():
                                # create the new channel at the right place
                                propertiesdict['channel_order'] = int(channelexists[str(current-1)])
                            else:
                                # create the new channel at the beginning
                                propertiesdict['channel_order'] = 0
                            break
                        current = current + 1
                    # create channel
                    core_TS3channel.channelcreate(channelname, propertiesdict)
                    numechannel = numechannel + 1
                if numechannel == 1 and numchannel == 0:
                    for key2 in channellist:
                        # if we found the empty subchannel from parent
                        if int(channellist[key2]['pid']) == config[key]['parent']:
                            if channellist[key2]['channel_name'][-2:] != '#1':
                                channelname = config[key]['subchan_name'].replace('[COUNT]', str(1))
                                # set channel properties
                                propertiesdict = {'channel_codec_quality': 10, 'channel_flag_maxclients_unlimited': 1, 'channel_flag_permanent': 1, 'cpid': config[key]['parent']}
                                propertiesdict.update(config[key]['channel_properties'])
                                core_TS3channel.channeldelete(key2)
                                core_TS3channel.channelcreate(channelname, propertiesdict)
        nextProof = time.time() + nextInterval
