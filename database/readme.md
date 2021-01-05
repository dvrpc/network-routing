# database

Create the SQL database necessary for this analysis by running:

```bash
python database/initial_setup.py
```

If you're on a computer behind the DVRPC firewall it will use a direct database connection to extract the raw data.

If you're outside the firewall, you'll need `wget` on your system path in order to run the script.
