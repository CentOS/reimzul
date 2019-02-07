#!/bin/bash

# This script is used to build a src.rpm from SCM/Git (CentOS !) before submitting it build 
# It will :
#  - git clone pkg
#  - position to correct branch/tag/commit
#  - call get_sources.sh and return_disttag.sh
#  - call rpmbuild to build the src.rpm

# Ensuring we exit non-zero as soon as something fails
set -e

function usage() {
cat << EOF

You need to call the script like this : $0 -arguments
 -p : Package to build a src.rpm for [required, example: httpd]
 -b : Git branch to use [required, example : c7]
 -c : Git tag/commit [optional, example: c56b744c9b851f31294d2b2eb25c01e597901baa]
 -s : Sources URL base path (defaults to https://git.centos.org/)
 -h : display this help
EOF

}

function varcheck() {
if [ -z "$1" ] ; then
        usage
        exit 1
fi
}

while getopts "hp:b:c:s:" option
do
  case ${option} in
    h)
      usage
      exit 1
      ;;
    p)
      pkg=${OPTARG}
      ;;
    b)
      git_branch=${OPTARG}
      ;;
    c)
      git_commit=${OPTARG}
      ;;
    s)
      git_url=${OPTARG}
      ;;
    ?)
      usage
      exit
      ;;
  esac
done

varcheck ${pkg}
varcheck ${git_branch}

if [ -z ${git_url} ]; then
  export git_url="https://git.centos.org"
fi

test -d ${pkg} && rm -Rf ${pkg}

# Git clone 
git clone ${git_url}/r/rpms/${pkg}.git
cd ${pkg}
git checkout ${git_branch}
test -d ~/git/centos-git-common || (mkdir ~/git; pushd ~/git ; git clone https://git.centos.org/r/centos-git-common.git ; popd)
# Downloading SOURCES
~/git/centos-git-common/get_sources.sh -q --surl ${git_url}/sources

# optional if we got a git hash/tag commit id
if [ ! -z ${git_commit} ] ;then
  git checkout ${git_commit}
fi

disttag=$(~/git/centos-git-common/return_disttag.sh)
srpm_path=$(rpmbuild -bs --nodeps --define "%_topdir `pwd`" --define "dist ${disttag}" SPECS/${pkg}.spec|cut -f 2 -d ':')
srpm_name=$(echo $srpm_path|rev|cut -f 1 -d '/'|rev)
echo "SRPM: $srpm_name"

