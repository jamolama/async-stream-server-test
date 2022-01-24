# README

## Overview

Sender server generates 100 files encoded as `int16`, writing ith file to `./out_send/<i>.bin`, and sending file over http to receiver server. File generation and transmission are non-blocking `asyncio` tasks.

Receiver server writes file to `out_recv/<i>.bin`, where `i` is included as a parameter to the http request.

## Install

Requires python >= 3.7

Clone project.

```sh
git clone https://github.com/jamolama/async-stream-server-test.git
cd async-stream-server-test
```

### Dependencies

Create a virtual environment for the project in the current directory.

```sh
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Running

Start the server that *receives data* (this is at `http://localhost:8080`)

```sh
# start receiver as a background process
python streamserver.py --server receiver&
```

Verify that background process is running.
```sh
jobs
[1]  + running    python streamserver.py --server receiver
```

Start the server that *sends data*
```sh
python streamserver.py --server sender
```

Kill background task when finished.
```sh
# get job id
jobs
[1]  + running    python streamserver.py --server receiver
# kill job using id
kill %1
```