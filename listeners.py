import pydle
import sleekxmpp

import clients
from bot import config

irc_clients = {}
xmpp_clients = {}

pool = pydle.ClientPool()

class ListenerIRC(pydle.Client):
    def on_connect(self):
        for channel in self.chans:
            self.join(channel)

    def on_message(self, channel, source, message):
        xmpp_clients[source].send_message(mto=self.dest.replace('[re]', channel),
                                          mbody=message,
                                          mtype='groupchat')

    def _create_user(self, nickname):
        pydle.BasicClient._create_user(self, nickname)

        if not nickname or '.' in nickname or '<' in nickname or nickname == 'NickServ':
            return

        for name, channel in self.channels.items():
            #if nickname in channel['users']:
            self.createXMPP(nickname, '#mopar')

    def on_join(self, channel, nickname):
        if nickname == self.username:
            return

        print('{} has joined {} (IRC)'.format(nickname, channel))
        self.createXMPP(nickname, channel)

    def on_part(self, user, message=None):
        if user == self.username:
            return

        print('{} has left ({}) (IRC)'.format(user, message))
        xmpp_clients[user].disconnect(wait=False)
        del xmpp_clients[user]

    def createXMPP(self, nickname, channel):
        if nickname in irc_clients:
            return

        xmpp_clients[nickname] = clients.ClientXMPP(
            jid='{}/{}'.format(config['xirc']['jabber']['jid'],
                               nickname),
            password=config['xirc']['jabber']['password'],
            conference=config['xirc']['jabber']['conference']['server'],
            prefix=config['xirc']['jabber']['conference']['prefix'],
            channel=channel,
            nick=nickname)
        if xmpp_clients[nickname].connect():
            xmpp_clients[nickname].process(block=False)


class ListenerXMPP(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, conference, nick, prefix, channels):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.conference = conference
        self.nick = nick
        self.use_ipv6 = False
        self.prefix = prefix
        self.channels = channels

        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0045')  # Multi-User Chat
        self.register_plugin('xep_0199')  # XMPP Ping

        self.add_event_handler('session_start', self.start)

        self.add_event_handler('groupchat_message', self.muc_message)

        for channel in channels:
            self.add_event_handler('muc::{}{}@{}::got_online'.format(prefix, channel,
                                                                   conference),
                                   self.online)
            self.add_event_handler('muc::{}{}@{}::got_offline'.format(prefix, channel,
                                                                    conference),
                                   self.offline)

    def muc_message(self, msg):
        channel = msg['from'].bare.replace('@' + self.conference, '')

        if self.prefix != '':
            channel = channel.replace(self.prefix, '')

        if msg['mucnick'] != self.nick and not msg['mucnick'] in xmpp_clients.keys():
            irc_clients[msg['mucnick']].message(channel, msg['body'])

    def start(self, event):
        self.get_roster()
        self.send_presence()

        for channel in self.channels:
            self.plugin['xep_0045'].joinMUC('{}@{}'.format(self.prefix + channel,
                                                           self.conference),
                                            self.nick)

    def online(self, presence):
        channel = presence['from'].bare.replace('@' + self.conference, '')

        if self.prefix != '':
            channel = channel.replace(self.prefix, '')

        if presence['muc']['nick'] != self.nick and not presence['muc']['nick'] in xmpp_clients:
            irc_clients[presence['muc']['nick']] = clients.ClientIRC(presence['muc']['nick'])
            irc_clients[presence['muc']['nick']].chan = channel
            pool.connect(irc_clients[presence['muc']['nick']],
                         config['xirc']['irc']['network'],
                         config['xirc']['irc']['port'],
                         tls=True)
            print('{} has joined {} (XMPP)'.format(presence['muc']['nick'], channel))

    def offline(self, presence):
        if presence['muc']['nick'] != self.nick and not presence['muc']['nick'] in xmpp_clients:
            irc_clients[presence['muc']['nick']].disconnect()
            del irc_clients[presence['muc']['nick']]
            print('{} has joined (XMPP)'.format(presence['muc']['nick']))
