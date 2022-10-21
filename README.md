# Simple Subreg.cz API simulator

The simulator of the Subreg.cz API implements just few methods fulfilling
needs of the Python [lexicon][lexicon] library.

The home page of the project is [here][subregsim-home].

[lexicon]: https://github.com/AnalogJ/lexicon
[subregsim-home]: https://github.com/oldium/subregsim

## Installation

Fetch the sources:

```
git clone -q https://github.com/oldium/subregsim.git
cd subregsim
```

Install dependencies:

```
pip install -r requirements.txt
```

Install subregsim Python package, including the `subregsim` binary (like in
`Dockerfile`):

```
pip install .
```

or in editable mode (like in `Dockerfile.development`):

```
pip install -e .
```


## Configuration

### Basic Setup

The configuration can be supplied in two ways:

1. See `subregsim.conf.sample`, copy it to `subregsim.conf` and change it to
   suite your needs. Use `-c subregsim.conf` argument to `subregsim`.

2. All configuration options can be supplied on command-line.

### SSL Setup

#### Local Certificate Authority

Generate self-signed certificate for your Certificate Authority (use your own
`subj` string):

```
openssl req -x509 -newkey rsa:4096 -nodes -keyout test-ca.key -sha256 -days 1825 -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=Test System CA" -out test-ca.csr
```

Now you have file `test-ca.key` with private key of Certificate Authority and
`test-ca.crt` with self-signed certificate. You can now import the `test-ca.crt`
file into your test system.

#### Domain Certificate

Now generate domain certificate, replace `example.com` with your domain (and use
your own `subj` string):

```
openssl req -newkey rsa:4096 -nodes -keyout server-certificate.key -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com" -out server-certificate.csr
```

The file `server-certificate.key` is the private key, the file
`server-certificate.csr` is certificate signing request.

#### Signed Domain Certificate

Now sign the request with your Certificate Authority:

```
openssl x509 -req -in server-certificate.csr -CA test-ca.crt -CAkey test-ca.key -CAcreateserial -out server-certificate.crt -days 1825 -sha256
```

The file `server-certificate.crt` (together with `server-certificate.key`) can now be used by the test server.

## Docker

### Production image

Build from sources (optional step - you can use official image):

```
docker build -t subregsim:latest .
```

Run as (uses `subregsim.conf` and generated certificates):

```
docker run --rm -it -v $PWD/server-certificate.crt:/config/server-certificate.crt -v $PWD/server-certificate.key:/config/server-certificate.key -v $PWD/subregsim.conf:/config/subregsim.conf subregsim:latest -c /config/subregsim.conf
```

### Development image

Build from sources:

```
docker build -t subregsim:develop-latest -f Dockerfile.development .
```

Run as (uses `subregsim.conf` and generated certificates):

```
docker run --rm -it -v $PWD/server-certificate.crt:/config/server-certificate.crt -v $PWD/server-certificate.key:/config/server-certificate.key -v $PWD/subregsim.conf:/config/subregsim.conf -v $PWD/.:/source subregsim:develop-latest -c /config/subregsim.conf
```

