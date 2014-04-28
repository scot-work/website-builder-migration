rm -rf ./people/*
rm -rf ./errors/*
rm migrate.log
rm people.zip
rm out.txt
python migrate.py all >> out.txt
cd people
zip -r archive.zip *
