#!/usr/bin/env bash

openshift_spark () {
  BRANCH=`echo ${VERSION} | grep -o '^[0-9]\.[0-9]'`
  # master_update
  branch_update
  tag_update
}

function master_update(){
  setup_wdir

  echo "Run change-yaml.sh"
  ./change-yaml.sh ${VERSION}

  echo "regenerate the *-build directory"
  make clean-context
  make context
  make zero-tarballs
  git add openshift-spark-build

  echo "Report the changes"
  git status
  git --no-pager diff --cached

  echo "Commit the changes to master branch"
  git commit -m "Spark version update for openshift-spark"

  if [ "${QUIET}" = "true" ] ; then
    echo
    echo "COMMAND OMITTED:"
    echo "git push https://<GITHUB_TOKEN>@github.com/${USER}/${REPO} master"
    echo
  else
    echo "### PUSHING TO REPO ${USER}/${REPO} master ###"
    # git push https://${GITHUB_TOKEN}@github.com/${USER}/${REPO} master
  fi
}

function branch_update(){
  echo "Create a new X.Y branch for the new spark version."
  git checkout -b ${BRANCH}
  if [ "${QUIET}" = "true" ] ; then
    echo
    echo "COMMAND OMITTED:"
    echo "git push https://<GITHUB_TOKEN>@github.com/${USER}/${REPO} ${BRANCH}"
    echo
  else
    echo "### PUSHING TO REPO ${USER}/${REPO} ${BRANCH} ###"
    git push https://${GITHUB_TOKEN}@github.com/${USER}/${REPO} ${BRANCH}
  fi
}

function tag_update(){
  echo "Tag the commit on a branch with X.Y.0-1"
  git checkout ${BRANCH}
  TAG=`./tag.sh | grep 'Adding tag *' | sed "s/Adding tag //g"`

  # Verify:
  ACTUAL_TAG=`git tag --list | head -n1`
  if [ "${TAG}" = "${ACTUAL_TAG}" ] ; then
    echo "Tag was successfully updated. Good to push."
  fi

  if [ "${QUIET}" = "true" ] ; then
    echo
    echo "COMMAND OMITTED:"
    echo "git push https://<GITHUB_TOKEN>@github.com/${USER}/${REPO} ${TAG}"
    echo
  else
    echo "### PUSHING TO REPO ${USER}/${REPO} ${TAG} ###"
    git push https://${GITHUB_TOKEN}@github.com/${USER}/${REPO} ${TAG}
  fi
}