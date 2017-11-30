#!/bin/bash

# This script accepts multiple parameters
# See usage() for required parameters

function usage() {
cat << EOF

You need to call the script like this : $0 -arguments
 -s : SRPM pkg to submit to mock
 -d : disttag to use in mock
 -t : mock target/config to use and push to 
 -a : architecture
 -h : display this help

EOF
}

function varcheck() {
if [ -z "$1" ] ; then
        usage
        exit 1
fi
}

while getopts "hs:d:t:a:" option
do
  case ${option} in
    h)
      usage
      exit 1
      ;;
    s)
      srpm_pkg=${OPTARG}
      ;;
    d)
      disttag=${OPTARG}
      ;;
    t)
      target=${OPTARG}
      ;;
    a)
      arch=${OPTARG}
      ;;
    ?)
      usage
      exit
      ;;
  esac
done

varcheck ${srpm_pkg}
varcheck ${disttag}
varcheck ${target}
varcheck ${arch}


tmp_dir=$(mktemp -d)
curl --silent http://localhost:11080/reimzul-incoming/${srpm_pkg} --output ${tmp_dir}/${srpm_pkg}
pkg_name=$(rpm -qp --queryformat '%{name}\n' ${tmp_dir}/${srpm_pkg})
evr=$(rpm -qp --queryformat '%{version}-%{release}\n' ${tmp_dir}/${srpm_pkg})
resultdir=/srv/build/logs/${target}/${pkg_name}/$(date +%Y%m%d%H%M%S)/${evr}.${arch}/
mkdir -p ${resultdir}
mock -r ${target} --configdir=/srv/build/config/ --resultdir=${resultdir} --define "dist ${disttag}" ${tmp_dir}/$srpm_pkg >> ${resultdir}/stdout 2>>${resultdir}/stderr
rsync -a --port=11874 /srv/build/logs/${target}/${pkg_name}/ localhost::reimzul-bstore/repo/${target}/${pkg_name}/
rm -Rf ${resultdir}
rm -Rf ${tmp_dir}
