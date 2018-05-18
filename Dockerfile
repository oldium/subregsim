# Dockerfile for production (sources taken from Git)
# 1. Build as: docker build -t subregsim:latest .
# 2. Prepare configuration file and certificates (both optional) - see argument "-c" in next step
# 3. Run as: docker run --rm -it -v $PWD/server-certificate.crt:/config/server-certificate.crt -v $PWD/server-certificate.key:/config/server-certificate.key -v $PWD/subregsim.conf:/config/subregsim.conf subregsim:latest -c /config/subregsim.conf

# Base image
FROM alpine:edge as base

RUN mkdir /python
ENV PYTHONUSERBASE=/python
ENV PATH="$PYTHONUSERBASE/bin:$PATH"

RUN apk add --no-cache python3~3.6 py3-openssl

# Build phase
FROM base as build

RUN mkdir /build
WORKDIR /build

RUN apk add --no-cache git py3-setuptools && \
	pip3 install --upgrade pip

RUN git clone -q https://github.com/oldium/subregsim.git && \
	cd subregsim && \
	pip3 install --user -r requirements.txt && \
	pip3 install --user .

# Final phase
FROM base

EXPOSE 80 443

COPY --from=build /python /python

ENTRYPOINT ["/python/bin/subregsim"]
CMD ["--help"]