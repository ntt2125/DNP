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

* Install [Pytorch](https://pytorch.org/) with gpu or not

* Because we use RTMPose from **mmPose** so follow the mmPose installation [here](https://mmpose.readthedocs.io/en/latest/installation.html) 

* `pip install ultralytics`

* `pip install confluent-kafka`


### Executing program

* Run confluent kafka docker `docker-compose.yaml` file.
```
docker compose up
```
* Open 3 terminal window and run this by order.

```
$ python producer.py

$ python detection_model.py

$ python consumer.py
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