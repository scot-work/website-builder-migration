rm -rf ./people/*
rm -rf ./errors/*
rm migrate.log
rm out.txt
python migrate.py steven.lee >> out.txt
python migrate.py nancy.stork >> out.txt
python migrate.py anand.vaidya >> out.txt
python migrate.py guadalupe.salazar >> out.txt
python migrate.py quincy.mccrary >> out.txt
python migrate.py mary.juno >> out.txt
python migrate.py carol.mukhopadhyay >> out.txt
python migrate.py tsau.lin >> out.txt
python migrate.py marcos.pizarro >> out.txt
python migrate.py gordon.haramaki >> out.txt
cd people
zip -r archive.zip * >> null
echo 'done'
