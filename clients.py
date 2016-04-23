import pydle
import sleekxmpp


class ClientIRC(pydle.Client):
    def on_connect(self):
        self.join(self.chan)


class ClientXMPP(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, conference, nick, prefix, channel):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.conference = conference
        self.nick = nick
        self.use_ipv6 = False
        self.prefix = prefix
        self.channel = channel

        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0045')  # Multi-User Chat
        self.register_plugin('xep_0199')  # XMPP Ping

        self.add_event_handler('session_start', self.start)

    def start(self, event):
        self.get_roster()
        self.send_presence()

        self.plugin['xep_0045'].joinMUC('{}@{}'.format(self.prefix + self.channel,
                                                       self.conference),
                                        self.nick)
