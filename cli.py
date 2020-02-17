#!/usr/bin/python3

import argparse
import getpass
import os

import gkeepapi

import keyring

keep = gkeepapi.Keep()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('note', type=str,
                        help='ID of note to act upon')
    parser.add_argument('--email', type=str, default=os.getenv('GMAIL', None),
                        help='email of keep notes owner: default $GMAIL')
    parser.add_argument('--token', type=str, default='google-keep-token',
                        help='name of token in keyring')
    args = parser.parse_args()

    note_id = args.note
    token_name = args.token
    email = args.email
    if not email:
        print('No email specified on CLI or $GMAIL')
        email = input('Enter email: ')

    auth(email, token_name)
    note = keep.get(note_id)

    # TODO - this is kinda ugly, need cleaner command def and validation
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        show_note(note)
        (command, param) = get_command()
        if command == 'exit':
            print('Bye!')
            exit()
        elif command == 'refresh':
            keep.sync()
        elif command == 'add':
            note.add(param, False)
            keep.sync()
        elif command == 'check':
            try:
                note.unchecked[int(param)].checked = True
                keep.sync()
            except (IndexError, TypeError):
                pass


def get_command():
    no_param = ['exit', 'refresh']
    one_param = ['add', 'check']
    commands = no_param + one_param

    user_input = input('Enter command: ').split(' ')
    command = user_input[0]
    param = ' '.join(user_input[1:]) if len(user_input) > 1 else None

    if command not in commands:
        print('Param %s is invalid %s' % (command, commands))
        return get_command()
    if command in one_param and not param:
        print('Command %s requires a parameter' % command)
        return get_command()
    return (command, param)


def show_note(note):
    print(note.title)
    index = 0
    for item in note.unchecked:
        print('%s: %s' % (index, item))
        index += 1
    print('')


def check_item(note, index):
    note.unchecked.checked = True


def add_item(note, text):
    # TODO - still adds items at top of list...
    note.add(text, False, gkeepapi.node.NewListItemPlacementValue.Bottom)


def auth(email, token_name):
    token = keyring.get_password(token_name, email)
    if not token:
        token = login(email, token_name)
    keep.resume(email, token)


def login(email, token_name):
    password = getpass.getpass('Enter password: ')
    try:
        keep.login(email, password)
    except gkeepapi.exception.LoginException as e:
        if e.args[0] == 'NeedsBrowser':
            print('MFA is enabed on this account, use app password: '
                  'https://support.google.com/accounts/answer/185833')
            exit()
        else:
            print(e.args[0])
            return login(email, token_name)
    token = keep.getMasterToken()
    keyring.set_password(token_name, email, token)
    return token


if __name__ == '__main__':
    main()
