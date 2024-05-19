# WebPyMail - IMAP python/django web mail client
# Copyright (C) 2008 Helder Guerreiro

# This file is part of WebPyMail.
#
# WebPyMail is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# WebPyMail is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hlimap.  If not, see <http://www.gnu.org/licenses/>.

#
# Helder Guerreiro <helder@tretas.org>
#

import imaplib

from django.contrib.auth.models import User


def generatePassword(password_len=40):
    """
    Generates a password password_len characters in lenght.

    @param password_len: lenght of the generated password
    @type password_len: int
    """
    VALID_CHARS = '1234567890qwertyuiopasdfghjklzxcvbnm,.-\'' \
                  '+!"#$%&/()=?QWERTYUIOP*ASDFGHJKL^ZXCVBNM;:_'
    from random import choice
    return ''.join([choice(VALID_CHARS) for i in range(password_len)])


class ImapBackend:
    """Authenticate using IMAP
    """

    def authenticate(self, request=None, username=None, password=None,
                     host=None, port=143, ssl=False):
        try:
            if ssl:
                M = imaplib.IMAP4_SSL(host, port)
            else:
                M = imaplib.IMAP4(host, port)
            M.login(username, password)
            M.logout()
            valid = True
        except M.error:
            valid = False

        if valid:
            try:
                user = User.objects.get(username=('%s@%s' %
                                                  (username, host))[:30])
            except User.DoesNotExist:
                # Create a new user
                password = generatePassword()
                user = User(username=('%s@%s' % (username, host))[:30],
                            password=password)
                user.is_staff = False
                user.is_superuser = False
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
