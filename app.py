from flask import Flask, render_template, json, request, redirect, url_for
from flaskext.mysql import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import pyodbc
import logging
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

app = Flask(__name__)

# Azure Key Vault Configuration
KEY_VAULT_NAME = "KV-WebApp-001"
KV_URI = f"https://KV-WebApp-001.vault.azure.net"

def get_secret(secret_name):
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KV_URI, credential=credential)
        secret = client.get_secret(secret_name)
        return secret.value
    except Exception as e:
        logging.error(f"Error retrieving secret '{secret_name}': {e}")
        raise

# AZURE SQL DATABASE configurations  dbserver-webapp.database.windows.net
DBSERVER = get_secret("DBSERVER")
DBNAME = get_secret("DBNAME")
DBUSER = get_secret("DBUSER")
DBPASSWORD = get_secret("DBPASSWORD")
DBDRIVER = '{ODBC Driver 17 for SQL Server}'  # Make sure this driver is installed

# Connection string for Azure SQL Database
connection_string = f'DRIVER={DBDRIVER};SERVER={DBSERVER};PORT=1433;DATABASE={DBNAME};UID={DBUSER};PWD={DBPASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Tineout=30;'


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/signup')
def showSignUp():
    return render_template('signup.html')


logging.basicConfig(level=logging.DEBUG)

@app.route('/api/signup', methods=['POST'])
def signUp():
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']
        print(f"Name: {_name}, Email: {_email}, Password: {_password}")  # Debugging line
        logging.debug(f"Name: {_name}, Email: {_email}, Password: {_password}")
        
        # validate the received values
        if _name and _email and _password:

            # All Good, let's call MySQL
            _hashed_password = generate_password_hash(_password)
        
            # Connect to Azure SQL Database
            conn = pyodbc.connect(connection_string)
            cursor = conn.cursor()
            logging.debug("Database Connection Established")
            
            # Call the stored procedure
            cursor.execute("EXEC sp_createUser @p_name = ?, @p_username = ?, @p_password = ?", 
                           (_name, _email, _hashed_password))
            conn.commit()
            logging.debug("User Inserted Successfully")

            print("User created successfully!")
            return redirect(url_for('home') + "?message=User%20created%20successfully!")
            

        else:
            return json.dumps({'html': '<span>Enter the required fields</span>'})    
            

    except Exception as e:
        logging.error(f"Error: {e}")
        return json.dumps({'error': str(e)})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    app.run(debug=True)
