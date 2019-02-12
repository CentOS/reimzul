
### Remote Reimzul client (from everywhere, no local access needed)

Assuming that you have a valid x509 TLS cert (from https://accounts.centos.org) and that your CN (username) is authorized for some builds/architectures), you can remotely use the client/reimzul_client python script
You need:
  - certificates/CA (usually obtained through centos-cert - centos-packager rpm package) 
  - python-paho-mqtt rpm installed (needed to submit to MQTT broker)
  - ~/.reimzul.ini file

Simple install steps:
```
sudo yum install -y python-paho-mqtt python2-configargparse centos-packager
test -d ~/bin || mkdir ~/bin
pushd ~/bin ; curl --location https://raw.githubusercontent.com/CentOS/reimzul/master/client/reimzul_client -O ; chmod +x reimzul_client ; popd
pushd ~ 
curl --location https://raw.githubusercontent.com/CentOS/reimzul/master/client/reimzul.ini.sample > .reimzul.ini
sed -i "s/<user>/$USER/g" .reimzul.ini
popd

```
Last step: put the correct mqtt broker hostname in that ~/.reimzul.ini file

Don't forget (if you don't have it already) to invoke `centos-cert` to retrieve your TLS cert


Then you can call the client like this :

```
usage: reimzul_client [-h] -p PKG -b GIT_BRANCH [-r GIT_REF] -a ARCH -t TARGET
                      [--scratch]

Reimzul CentOS distributed build remote client

optional arguments:
  -h, --help            show this help message and exit
  -p PKG, --package PKG
                        The package name to build, coming from SCM/Git
                        [example: httpd]
  -b GIT_BRANCH, --branch GIT_BRANCH
                        The Git branch to build the src.rpm from [example: c7]
  -r GIT_REF, --ref GIT_REF
                        The Git commit/ref to specifially use (default: HEAD)
  -a ARCH, --arch ARCH  Defines the mock architecture to build against
                        [example: x86_64,armhfp,aarch64,i386,ppc64le,ppc64]
  -t TARGET, --target TARGET
                        The target repo to build against/for, without any arch
                        specified [example: c7.1708.u]
  --scratch             Will just build the pkg but not prepare it in staging-
                        tosign area

``` 



