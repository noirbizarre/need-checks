#!/usr/bin/env sh

VERSION=${CZ_POST_CURRENT_VERSION}

# Create or update MAJOR and MAJOR.MINOR tags
MAJOR_MINOR=${VERSION%.*}
echo "Tagging <major>.<minor> version ${MAJOR_MINOR}" >&2
git tag -fa "${MAJOR_MINOR}" -m "Update major.minor version tag"
git push origin "${MAJOR_MINOR}" --force

MAJOR=${VERSION%%.*}
if [ "${MAJOR}" != "0" ]; then
    echo "Tagging <major> version ${MAJOR}" >&2
    git tag -fa "${MAJOR}" -m "Update major version tag"
    git push origin "${MAJOR}" --force
fi


# Prepare next dev version
echo "Prepare next development cycle" >&2
sed -i "s/${VERSION}/main/g" action.yml
sed -i "s/${VERSION}/main/g" README.md
git commit -am "build: prepare next \`main\` version"
git push
