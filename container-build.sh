#! /bin/bash
export DOCKER_BUILDKIT=1

kvuser=kvalobs
kvuserid=5010
mode="test"
target=kvmodelpopulate
default_os=noble
os=noble
registry="registry.met.no/met/obsklim/bakkeobservasjoner/data-og-kvalitet/kvalobs/kvbuild"
nocache=
BUILDDATE=$(date +'%Y%m%d')
VERSION="$(./version.sh)"
tag="$VERSION"
tags=""
kvcpp_tag=latest
tag_counter=0
push="true"
build="true"
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
                Creates three tags: ${VERSION}, latest and a ${VERSION}-${BUILDDATE}.
                If the enviroment variable KV_BUILD_DATE is set use
                this as the build date. Format KV_BUILD_DATE YYYYMMDD.
  --tag-and-latest tagname tag the image with the name tagname  and also create latest tag.
  --build-only  Stop after building.
  --push-only   Push a previous build to registry. Must use the same flags as when building.
  --kvcpp-tag tagname Use tagname. Default: $kvcpp_tag (Not used, only for consistency)
  --staging     build and push to staging.
  --prod        build and push to prod.
  --test        only build, default
  --no-cache    Do not use the docker build cache.
  --print-version-tag
                Print the version tag and exit.

  The following opptions is mutally exclusive: --tag, --tag-and-latest and --tag-with-build-date
  The following options is mutally exclusive: --build-only, --push-only
  The following options is mutally exclusive: --staging, --prod, --test
"
echo -e "$usage\n\n"

}

while test $# -ne 0; do
  case $1 in
    --tag) 
        tag=$2
        shift
        tag_counter=$((tag_counter + 1))
        ;;
    --tag-and-latest) 
        tag="$2"
        tags="latest"
        tag_counter=$((tag_counter + 1))
        shift
        ;;
    --help) 
      use
      exit 0;;
    --kvcpp-tag) 
        kvcpp_tag=$2;
        shift;;
    --staging) mode="staging";;
    --prod) mode="prod";;
    --test) mode="test";;
    --tag-with-build-date)
        tags="latest $VERSION-$BUILDDATE"
        tag_counter=$((tag_counter + 1))
        ;;
    --no-cache) nocache="--no-cache";;
    --build-only)
        push="false";;
    --push-only)
        build="false";;

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

if [ $tag_counter -gt 1 ]; then
  echo "Only one of --tag, --tag-and-latest or --tag-with-build-date can be used"
  exit 1
fi

echo "tag: $tag"
echo "tags: $tags"
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
if [ "$build" = "true" ]; then
  docker build $nocache --build-arg REGISTRY=${registry} \
    --build-arg "kvuser=$kvuser" --build-arg "kvuserid=$kvuserid" \
    -f Dockerfile --tag "${registry}${target}:${tag}" .

  for tagname in $tags; do
    echo "Tagging: ${registry}${target}:$tagname"
    docker tag "${registry}${target}:$tag" "${registry}${target}:$tagname"
  done
fi

if [ "$mode" != "test" ] && [ "$push" = "true" ]; then
  tags="$tag $tags"
  for tagname in $tags; do
      echo "Pushing: ${registry}${target}:$tagname"
      docker push "${registry}${target}:$tagname"
  done
fi
