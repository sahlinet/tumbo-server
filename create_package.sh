find . -name templates|cut -c3- | awk '{print "recursive-include "$0" *"}' > MANIFEST.in
find . -name static|cut -c3- | awk '{print "recursive-include "$0" *"}' >> MANIFEST.in
find . -name compose-files|cut -c3- | awk '{print "recursive-include "$0" *"}' >> MANIFEST.in

echo "recursive-include compose-files *" >> MANIFEST.in
echo "include ./requirements.txt" >> MANIFEST.in
echo "recursive-include . templates" >> MANIFEST.in
#python setup.py sdist
#python setup.py sdist --formats=gztar upload -r pypitest  --show-response
python setup.py sdist --formats=gztar upload -r pypitest  

echo "pip install --upgrade -i https://testpypi.python.org/pypi tumbo-server"
