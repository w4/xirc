import logging

import yaml

import listeners

logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

with open('config.yml') as file:
    config = yaml.load(file)

def main():
    xmpp = listeners.ListenerXMPP(jid='{}/{}'.format(config['xirc']['jabber']['jid'],
                                                     config['xirc']['jabber']['resource']),
                                  password=config['xirc']['jabber']['password'],
                                  conference=config['xirc']['jabber']['conference']['server'],
                                  prefix=config['xirc']['jabber']['conference']['prefix'],
                                  channels=config['xirc']['irc']['channels'],
                                  nick=config['xirc']['jabber']['nick'])

    irc = listeners.ListenerIRC(config['xirc']['irc']['nick'])
    irc.chans = config['xirc']['irc']['channels']
    irc.dest = '{}[re]@{}'.format(config['xirc']['jabber']['conference']['prefix'],
                                  config['xirc']['jabber']['conference']['server'])

    if xmpp.connect():
        xmpp.process(block=False)

    listeners.pool.connect(irc,
                           config['xirc']['irc']['network'],
                           config['xirc']['irc']['port'],
                           tls=True)
    listeners.pool.handle_forever()


if __name__ == '__main__':
    main()
