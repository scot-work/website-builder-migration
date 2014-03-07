rm -rf ./people/*
rm -rf ./errors/*
rm people.zip
rm out.txt
python migrate.py >> out.txt
cd people
zip -r archive.zip *
