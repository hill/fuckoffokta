# fuckoffokta

> Get TOPT secret from Okta QR code

I would rather use 1password than the okta app as I am lazy and don't want to walk to my phone.

Okta uses TOPT under the hood, we can extract the `sharedSecret` and then give that to 1password (or TOPT manager of your choice).

## Usage

**Read the code before doing anything. Don't just pass secrets to scripts you found on the internet.**

Install dependencies into virtualenv with `pipenv install`

Activate shell `pipenv shell`

Register a new "okta" device and take a screenshot of the QR code that appears on this device registration screen:

<center>
  <img src="./assets/registration.png" width="250" />
</center>

Run:

`python3 getTOPT.py <okta_qr_code_image>`


Add the TOPT secret that appears to your password manager.
(For 1password, add the secret into the field that appears under `edit > add more > one time password`)

You can now choose "enter a code" as an authenticaiton option and let 1password autofill the field with your OTP.

<center>
  <img src="./assets/auth.png" width="250" />
</center>