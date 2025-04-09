#! /bin/bash
export DOCKER_BUILDKIT=1

kvuser=kvalobs
kvuserid=5010
mode="test"
target=kvmodelpopulate
tag=latest
tag_and_latest=false
default_os=focal
os=noble
#os=bionic
registry="registry.met.no/met/obsklim/bakkeobservasjoner/data-og-kvalitet/kvalobs/kvbuild"
nocache=
BUILDDATE=$(date +'%Y%m%d')
VERSION="$(./version.sh)"
KV_BUILD_DATE=${KV_BUILD_DATE:-}

if [ -n "${KV_BUILD_DATE}" ]; then
  BUILDDATE=$KV_BUILD_DATE
fi

#
#docker build --build-arg REGISTRY=registry.met.no/obs/kvalobs/kvbuild/staging/ -t registry.met.no/obs/kvalobs/kvbuild/staging/kvaggregated .    
#docker push registry.met.no/obs/kvalobs/kvbuild/staging/kvaggregated
#
use() {

  usage="\
Usage: $0 [--help] [--no-cache] [--staging|--prod|--test] [--tag tag] [--tag-with-build-date] 

This script build a kvagregated container. 

If --staging or --prod is given it is copied to the 
container registry at $registry. 
If --test, the default, is used it will not be copied 
to the registry.


Options:
  --help        display this help and exit.
  --tag tagname tag the image with the name tagname, default latest.
  --tag-with-build-date 
                tag with version and build date on the form version-YYYYMMDD 
                and set latest. If the enviroment variable KV_BUILD_DATE is set use
                this as the build date. Format KV_BUILD_DATE YYYYMMDD.
  --tag-version Use version from configure.ac as tag. Also tag latest
  --staging     build and push to staging.
  --prod        build and push to prod.
  --test        only build, default
  --no-cache    Do not use the docker build cache.
  --print-version-tag
                Print the version tag and exit.

"
echo -e "$usage\n\n"

}

while test $# -ne 0; do
  case $1 in
    --tag) 
        tag=$2
        shift
        ;;
    --help) 
      use
      exit 0;;
    --staging) mode="staging";;
    --prod) mode="prod";;
    --test) mode="test";;
    --tag-with-build-date)
        tag="$VERSION-$BUILDDATE"
        tag_and_latest=true;;
    --tag-version) 
        tag="$VERSION"
        tag_and_latest=true;;
    --no-cache) nocache="--no-cache";;
    --print-version-tag)
        echo "$VERSION-$BUILDDATE"
        exit 0;;
    -*) use
      echo "Invalid option $1"
      exit 1;;  
    *) targets="$targets $1";;
  esac
  shift
done


echo "tag: $tag"
echo "mode: $mode"
echo "os: $os"
echo "Build mode: $mode"

if [ $mode = test ]; then 
  registry="$os/"
elif  [ "$os" = "$default_os" ]; then
  registry="$registry/$mode/"
else 
  registry="$registry/$mode-$os/"
fi

echo "registry: $registry"

docker build $nocache --build-arg REGISTRY=${registry} \
  --build-arg "kvuser=$kvuser" --build-arg "kvuserid=$kvuserid" \
  -f Dockerfile --tag "${target}:${tag}" .

docker tag "${target}:$tag" "${target}:latest"

if [ "$mode" != "test" ]; then 
  docker tag "${target}:${tag}" "${registry}${target}:${tag}"
  docker push "${registry}${target}:${tag}"
  
  if [ "$tag_and_latest" = "true" ]; then
    docker tag "${registry}${target}:${tag}" "${registry}${target}:latest"
    docker push "${registry}${target}:latest"
  fi
fi


