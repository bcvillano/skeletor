# Skeletor
Skeletor is a HTTP(S) C2 built upon the Flask framework designed for red vs. blue cybersecurity competitions. Use only on systems which you own or are authorized to deploy on.  
Skeletor implants communicate on a beaconing system, sending outbound POST requests to the Skeletor server's **/tasks** route at specified intervals to retrieve their tasks from the queue, execute them and send back the result
## Quickstart
### Setting Up Server
Copy  the provided .env.sample file to .env and edit the values for your desired configuration (see environment variables section of README for more details)  

#### HTTP
Update DB_USER and DB_PASSWORD environment variables in docker-compose.yml, then run:
```
docker compose up -d
```

#### HTTPS
- cd into the https/ directory  
- Update DB_USER and DB_PASSWORD environment variables in docker-compose.yml  
- Either run certgen.sh to generate self-signed certificates, or place certificates in the certs/ directory
- Run:
    ```
    docker compose up -d
    ```

### Configuring Implants
#### Go
Implant settings are defined in the Agent struct at the top of the main function of main.go in the implants/go directory
```
agent := Agent{
		LocalIP:          getLocalIP(),
		ServerIP:         "127.0.0.1",
		ServerPort:       443,
		CallbackInterval: 15,
		Jitter:           5,
		Debug:            false,
		Client: &http.Client{
			Timeout: 10 * time.Second,
		},
		Https: true,
	}
```
Configurable settings:
- ServerIP - set to value of server's IP address / domain name
- ServerPort - port the server is listening on
- CallbackInterval - time in seconds between callbacks to Skeletor C2 server
- Jitter - callback intervals will be randomized if greater than 0 and occur between (CallbackInterval - Jitter) and (CallbackInterval + Jitter) seconds
- Debug - Should be set to false usually, output error messages if set to true
- Https - boolean for whether to use HTTPS instead of unencrypted HTTP  

After setting desired configuration, compile using Makefile or *go build*
#### Python

```
    beacon = Beacon("127.0.0.1",port=443,callback_interval=15,jitter=7,https=True)
```
Configurable paramaters:
- server_ip - Required paramater, set to server IP address / domain name
- port - defaults to port 80, set to port server is listening on
- callback_interval - defaults to 120, seconds between callbacks
- jitter - defaults to 5, actual callback interval = randomied amount of seconds between (callback_interval - jitter) and (callback_interval + jitter)
- debug - defaults to false, if true prints debugging messages
- https - defaults to false, specififies whether to use https instead of unencrypted http

The *requests* library is required on the host the implant is run on to send the outbound HTTP(S) requests

