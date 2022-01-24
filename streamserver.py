from http.server import HTTPServer, BaseHTTPRequestHandler
import numpy as np
import time
import argparse
import asyncio
import requests
import pathlib
from urllib.parse import urlparse, parse_qs

# goal: over the course of 10 minutes, generate 100 binary files of random sizes ranging from 1kb to 1Mb at random time intervals ranging from 1ms to 1s, encoded int16.

port_receiver = 8080
# Data size must be between 1kb and 1Mb
data_size_min = 2**10 # 1kb
data_size_max = 2**20 # 1Mb
file_count = 100
duration_max = 10*60 # 10 min
# generate files at random intervals between 1ms and 1s
gen_interval_min = 1/1000.0 # 1ms
gen_interval_max = 1.0 # 1s
file_path_sender = pathlib.Path("out_send")
file_path_receiver = pathlib.Path("out_recv")
# create paths if don't exist
file_path_sender.mkdir(parents=True, exist_ok=True)
file_path_receiver.mkdir(parents=True, exist_ok=True)
# testing
test_delay_queue = False # asyncio tasks may always complete before next task submitted.
                        # Set to True to add artificial delay to each task to
                        #  test that asyncio task queue is resizing correctly


class DataGenerator:
    @staticmethod
    def generate(bit_count:int)->bytes:
        # as test we just use an array of ascending int16 values. Don't worry about overflow
        count = bit_count // 16
        vals = np.zeros(count, dtype=np.int16)
        for i in range(count):
            vals[i] = i
        return vals.tobytes()

# ServerSender generates data and sends it to ServerReceiver
class ServerSender:
    def __init__(self):
        self.task_count = 0

    def queue_size(self):
        # don't include calling task in queue size
        return len(asyncio.all_tasks())-1

    def completed_count(self):
        return self.task_count-self.queue_size()

    async def gen_send_task(self,task_id):
        data_size = np.random.randint(data_size_min, data_size_max)
        data = DataGenerator.generate(bit_count=data_size)
        start = time.time()
        # send data to receiver server
        response = requests.post(f"http://localhost:{port_receiver}", params={"task_id":task_id}, data=data)
        # write file to disk
        file_name = file_path_sender.joinpath(f"{task_id}.bin")
        with open(file_name, "wb") as f:
            f.write(data)

        if test_delay_queue:
            await asyncio.sleep(1)
        duration = time.time() - start
        print(f"SENDER task {task_id} finished (sent {data_size/(1024*8):0.2f} kB, duration {duration*1000:0.2f} ms)")

    async def run(self):
        end_time = time.time() + duration_max
        # run for duration_max seconds or until all files generated and transferred
        while time.time() < end_time and self.task_count < file_count:
            await asyncio.sleep(np.random.uniform(low=gen_interval_min, high=gen_interval_max))
            task_id = self.task_count
            asyncio.create_task(self.gen_send_task(task_id))
            self.task_count += 1
            print(f"SENDER: created task {task_id}, queue size: {self.queue_size()}, tasks completed: {self.completed_count()}")

        await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})
        print(f"SENDER: generated and sent {self.task_count} files")

class ServerReceiver(BaseHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length'))
        post_body = self.rfile.read(content_length)
        data = np.frombuffer(post_body, dtype=np.int16)
        params = parse_qs(urlparse(self.path).query)
        task_id = params["task_id"][0]
        self.send_response(200)
        self.end_headers()
        # write received data to disk
        file_name = file_path_receiver.joinpath(f"{task_id}.bin")
        with open(file_name, "wb") as f:
            f.write(data)
        print(f"RECEIVER: received task {task_id}")

def run_receiver():
    httpd = HTTPServer(('localhost',port_receiver),ServerReceiver)
    httpd.serve_forever()


def run_sender():
    sender = ServerSender()
    asyncio.run(sender.run())

def main():
    parser = argparse.ArgumentParser(description='run a server that generates data or a server that receives data')

    parser.add_argument('--server',type=str, choices=["sender", "receiver"], help='arghelp')
    args = parser.parse_args()
    if args.server == "sender":
        run_sender()
    elif args.server == "receiver":
        run_receiver()
    else:
        print("Invalid argument")


if __name__ == '__main__':
    main()