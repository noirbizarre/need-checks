#!/usr/bin/env sh

# Replace latest tag by the bumped version in action.yml
sed -i "s/main/${CZ_PRE_NEW_VERSION}/g" action.yml
