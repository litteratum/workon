# Integration tests

Currently, to run integration tests, these steps should be performed:

* Start `gogs` in the Docker container using the following command:

  ```bash
  docker run --rm --name gogs -p 3000:3000 gogs/gogs
  ```

* Go to `http://127.0.0.1:3000/install` and finish up install steps for first-time run
  * Change only DB credentials, you can use Docker `postgres` image
* Sign up and then sign in
* Create two empty repositories named `a` and `b`
* Run `make test_integration`
