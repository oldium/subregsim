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

Create a virtual environment and install the project:

```
uv sync
```

For a quick start, run the simulator without any arguments. It will use:

- domain: `example.com`
- username: `username`
- password: `password`

```
uv run subregsim
```

The installed console script and `python -m subregsim` use the same runtime
entrypoint and error handling.

## Configuration

### Basic Setup

The configuration can be supplied in two ways:

1. See `subregsim.conf.example`, copy it to `subregsim.conf` and change it to
   suite your needs. Use `-c subregsim.conf` argument to `subregsim`.

2. All configuration options can be supplied on command-line.

If you do not provide `domain`, `username`, or `password`, the simulator uses
defaults: `example.com`, `username`, and `password`.

The simulator can serve multiple domains. On the command-line, repeat the
`--domain` option (e.g. `--domain example.com --domain example.net`). In the
config file or in the `SUBREGSIM_DOMAIN` environment variable, pass a list,
for example `[example.com, example.net, example.org]`.

Basic run example with configuration file:

```
subregsim -c subregsim.conf
```

The simulator currently uses the Spyne-based SOAP server implementation.

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

Run with HTTPS enabled:

```
subregsim -c subregsim.conf --ssl --ssl-certificate server-certificate.crt --ssl-private-key server-certificate.key
```

### Local DNS server

The simulator can also run a local DNS server alongside the SOAP API.

When enabled with `--dns`, it serves the simulated zone contents generated from
the current in-memory API state, including DNS records added through the
simulated Subreg API.

Example:

```
subregsim -c subregsim.conf --dns --dns-host 127.0.0.1 --dns-port 53
```

You can combine both HTTPS and DNS:

```
subregsim -c subregsim.conf --ssl --ssl-certificate server-certificate.crt --ssl-private-key server-certificate.key --dns
```

## Docker

Build the image:

```
docker build -t subregsim:latest .
```

The image follows the current `uv` recommendation for containers: install
dependencies in a cached layer with
`uv sync --locked --no-install-project --no-dev --no-editable`, then install
the project separately and copy only the resulting virtual environment into the
final runtime image. The runtime container switches to `/config`, so a relative
config path such as `subregsim.conf` works directly there.

> [!NOTE]
> The release image can be built in a more trustable way with the following
> command, which ensures that fresh third-party images are used and adds
> provenance and SBOM metadata to the Docker image itself:
>
> ```
> docker buildx build --progress=plain --attest type=provenance,mode=max \
>   --attest type=sbom,generator=docker/scout-sbom-indexer:latest \
>   --pull --no-cache -f ./Dockerfile . -t subregsim:latest
> ```

Run it with a mounted config file and optional certificates, for example with
HTTPS exposed on port `443`:

```
docker run --rm -it \
  -p 443:443 \
  -v ./server-certificate.crt:/config/server-certificate.crt \
  -v ./server-certificate.key:/config/server-certificate.key \
  -v ./subregsim.conf:/config/subregsim.conf \
  subregsim:latest -c subregsim.conf
```

This also means certificate paths inside `subregsim.conf` can stay relative
when the files are mounted into `/config`.

If you also want to expose the DNS server, publish port `53` for both UDP and
TCP. For example, if `subregsim.conf` enables both SSL and DNS:

```
docker run --rm -it \
  -p 443:443 \
  -p 53:53/udp \
  -p 53:53/tcp \
  -v ./server-certificate.crt:/config/server-certificate.crt \
  -v ./server-certificate.key:/config/server-certificate.key \
  -v ./subregsim.conf:/config/subregsim.conf \
  subregsim:latest -c subregsim.conf
```
