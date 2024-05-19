# Secure Email Client

## Description
Secure Email Client is an email client based on python language.

## Python version
`$ python --version`\
`Python 3.8.5`

## How to run
1. Install all python dependencies in `requirements.txt` and `requirements-plugins.txt`.
   Use command below:
    ```
    pip install -r requirements.txt
    pip install -r requirements-plugins.txt
    ```
3. Run `./prepare.sh` to generate database used by the application.
4. Run `./server.sh` to start mail client server.
5. Access the url showed by Django (by default it is `http://127.0.0.1:8000/`) via browser in your desktop.
6. On login page select `Google Gmail` for the `Imap Server`.
7. Login to the mail client using your Gmail account. To setup IMAP access on Gmail and turn on Less Secure Apps see articles on **Notes to Setup Gmail Account** below.
