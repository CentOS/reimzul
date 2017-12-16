#!/bin/bash

# This script accepts multiple parameters
# See usage() for required parameters

# Some variables
reimzul_basedir="/srv/reimzul/"
bstore_baseurl="http://localhost:11081/bstore"

function usage() {
cat << EOF

You need to call the script like this : $0 -arguments
 -s : SRPM pkg to submit to mock
 -d : disttag to use in mock
 -t : mock target/config to use and push to 
 -a : architecture
 -p : timestamp for the resultdir
 -h : display this help
EOF
}

function varcheck() {
if [ -z "$1" ] ; then
        usage
        exit 1
fi
}

while getopts "hs:d:t:a:p:" option
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
    p)
      timestamp=${OPTARG}
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
varcheck ${timestamp}


pkg_name=$(rpm -qp --queryformat '%{name}\n' ${tmp_dir}/${srpm_pkg})
evr=$(rpm -qp --queryformat '%{version}-%{release}\n' ${tmp_dir}/${srpm_pkg})
resultdir=${reimzul_basedir}/results/${target}/${pkg_name}/${timestamp}/${evr}.${arch}/
mkdir -p ${resultdir}


# Import needed mock config files and replacing baseurl
cp ${reimzul_basedir}/mock_configs/mock/{site-defaults.cfg,logging.ini} ${resultdir}

if [ -e "${reimzul_basedir}/mock_configs/mock/${pkg_name}.cfg" ] ; then
  mock_cfg="${reimzul_basedir}/mock_configs/mock/${pkg_name}.cfg"
else
  mock_cfg="${reimzul_basedir}/mock_configs/mock/${target}.cfg"
fi

cat ${mock_cfg} | sed "s#http://repohost#${bstore_baseurl}#" | sed "s#TARGETNAME#${target}-${timestamp}#" > ${resultdir}/mock.cfg

mock -r mock --configdir=${resultdir} --resultdir=${resultdir} --define "dist ${disttag}" --cleanup-after ${tmp_dir}/$srpm_pkg >> ${resultdir}/stdout 2>>${resultdir}/stderr
export mock_exit_code="$?"

# Checking if {build,root}.log exist
for file in build.log root.log ; do
  test -f ${resultdir}/${file} || cp ${resultdir}/stderr ${resultdir}/${file}
done
rsync -a --port=11874 ${reimzul_basedir}/results/${target}/${pkg_name}/ localhost::reimzul-bstore/repo/${target}/${pkg_name}/
rm -Rf ${reimzul_basedir}/results/${target}/${pkg_name}/${timestamp}
exit ${mock_exit_code}
