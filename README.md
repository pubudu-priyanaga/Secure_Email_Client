# Email Client

Secure Email Client is an email client based on python language.



### Contribution

IT21184758 - Liyanage P.P.\
IT21170720 - Jayawickrama K.D.S.P.


### Prerequisites

Install the following prerequisites:

1. [Python 3.8-3.11](https://www.python.org/downloads/)
<br> This project uses **Django v4.2.4**. For Django to work, you must install a correct version of Python on your machine. More information [here](https://django.readthedocs.io/en/stable/faq/install.html).
2. [Visual Studio Code](https://code.visualstudio.com/download)


### Installation

#### 1. Create a virtual environment

From the **root** directory, run:

```bash
python -m venv venv
```

#### 2. Activate the virtual environment

From the **root** directory, run:

On macOS:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\scripts\activate
```

#### 3. Install required dependencies

From the **root** directory, run:

```bash
pip install -r requirements.txt
```

#### 4. Run migrations

From the **root** directory, run:

```bash
python manage.py makemigrations
```
```bash
python manage.py migrate
```


### Run the application

From the **root** directory, run:

```bash
python manage.py runserver
```


### View the application

Go to http://127.0.0.1:8000/ to view the application.


### Note

Just remember to send an email to an email address that already exists in the database.
