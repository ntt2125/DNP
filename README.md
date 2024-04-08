# Project Title

DNP project.
## Description
Re-produce a system to detection, tracking and analysis student action.


## Getting Started

### Dependencies

* OS: **Ubuntu 22.04**.
* **Docker**, **Cuda 12.1** (cpu is oke but slower)
* **Pytorch 2.1**
* [Confluent kafka](https://kafka-python.readthedocs.io/en/master/apidoc/KafkaConsumer.html#kafka.KafkaConsumer.poll)
* **MUST** have more than 8gb of RAM
* Familiar with [**Openmmlab**](https://github.com/open-mmlab), [**mmTracking**](https://github.com/open-mmlab/mmtracking), [**mmPose**](https://github.com/open-mmlab/mmpose), [**Ultralytics**](https://github.com/ultralytics/ultralytics)



### Installing

```
$ pip3 install torch torchvision torchaudio
$ pip install -U openmim
$ mim install mmengine
$ pip install -r requirements.txt
```


### Executing program

* Run confluent kafka docker `docker-compose.yaml` file.
```
docker compose up
```
* Create topics first: `python create_topics.py`

* Open 4 terminal window and run this by order.

```
$ python Save_video_process.py
$ python Pose_process.py
$ python Tracking_process.py
$ python Read_frame_process.py
```

* Or just one line
```
$ chmod +x run_local.sh
$ ./run_local.sh

```

## Help

Any advise for common problems or issues.
```
God bless you :)
```

## Authors

Contributors names and contact info


* [@NTThong](https://twitter.com/tthong59964726)

## Version History

* 0.2
    * Various bug fixes and optimizations
    * See [commit change]() or See [release history]()
* 0.1
    * Initial Release

## License

This project is licensed under the [NAME HERE] License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* [awesome-readme](https://github.com/matiassingers/awesome-readme)
* [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* [dbader](https://github.com/dbader/readme-template)
* [zenorocha](https://gist.github.com/zenorocha/4526327)
* [fvcproductions](https://gist.github.com/fvcproductions/1bfc2d4aecb01a834b46)