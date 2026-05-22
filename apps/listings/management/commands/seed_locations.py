"""
Management command: seed_locations
Populates all 47 Kenyan counties, major towns, and estates/areas.
Safe to run multiple times — uses get_or_create (no duplicates).
Run: python manage.py seed_locations
"""

from django.core.management.base import BaseCommand
from apps.listings.models import County, Town, Estate


DATA = {
    "Nairobi": {
        "Nairobi CBD": [
            "CBD", "Upper Hill", "Ngara", "Pangani", "Mlango Kubwa",
            "Industrial Area", "Eastleigh", "Kamukunji",
        ],
        "Westlands": [
            "Westlands", "Parklands", "Highridge", "Lower Kabete", "Kangemi",
            "Loresho", "Mountain View", "Kitisuru", "Muthaiga",
        ],
        "Kilimani": [
            "Kilimani", "Lavington", "Valley Arcade", "Adams Arcade",
            "Woodley", "Dagoretti", "Kawangware",
        ],
        "Karen & Langata": [
            "Karen", "Langata", "Nairobi West", "South B", "South C",
            "Hardy", "Rongai", "Ngong",
        ],
        "Eastlands": [
            "Umoja", "Donholm", "Komarock", "Embakasi", "Utawala",
            "Pipeline", "Buruburu", "Kayole", "Njiru", "Ruai",
            "Githurai 44", "Githurai 45", "Mwiki", "Kasarani",
            "Roysambu", "Clay City", "Huruma", "Mathare",
        ],
        "Thika Road": [
            "Kahawa West", "Kahawa Wendani", "Garden Estate", "Allsopps",
            "Ruaraka", "Zimmerman", "Muthaiga North", "Ridgeways",
            "Mirema", "TRM Area",
        ],
        "Ruiru & Juja": [
            "Ruiru Town", "Kamakis", "Eastern Bypass", "Juja Town",
            "Kalimoni", "Murera",
        ],
        "Thika Town": [
            "Thika Town", "Makongeni", "Gatuanyaga", "Ngoigwa",
            "Kiandutu", "Biashara",
        ],
    },
    "Mombasa": {
        "Mombasa Island": [
            "CBD Mombasa", "Old Town", "Tudor", "Majengo", "Tononoka",
        ],
        "Nyali & Bamburi": [
            "Nyali", "Bamburi", "Shanzu", "Mtwapa", "Kisauni",
            "Bombolulu", "Mkomani",
        ],
        "Likoni": [
            "Likoni", "Shelly Beach", "Mtongwe", "Bofu",
        ],
        "Changamwe & Mikindani": [
            "Changamwe", "Mikindani", "Port Reitz", "Miritini",
            "Chaani", "Magongo",
        ],
        "Kwale Border": [
            "Diani Beach", "Ukunda", "Msambweni", "Shimba Hills",
        ],
    },
    "Kisumu": {
        "Kisumu Town": [
            "Kisumu CBD", "Milimani", "Lolwe", "Nyamasaria",
            "Mamboleo", "Kondele", "Manyatta", "Obunga",
        ],
        "Ahero & Muhoroni": [
            "Ahero", "Muhoroni", "Chemelil",
        ],
        "Maseno": [
            "Maseno", "Luanda", "Kombewa",
        ],
    },
    "Nakuru": {
        "Nakuru Town": [
            "Nakuru CBD", "Section 58", "Milimani", "London",
            "Lanet", "Mwariki", "Kaptembwa", "Flamingo",
            "Shabab", "Free Area", "Barnabas",
        ],
        "Naivasha": [
            "Naivasha Town", "Kongoni", "Gilgil", "Elementaita", "Karati",
        ],
        "Molo & Njoro": [
            "Molo Town", "Njoro Town", "Elburgon",
        ],
    },
    "Kiambu": {
        "Kiambu Town": [
            "Kiambu Town Centre", "Ndumberi", "Tinganga",
        ],
        "Kikuyu": [
            "Kikuyu Town", "Kinoo", "Wangige", "Banana", "Sigona", "Ondiri",
        ],
        "Limuru": [
            "Limuru Town", "Tigoni", "Kimende", "Uplands",
        ],
        "Ruaka & Ruiru": [
            "Ruaka", "Ndenderu", "Two Rivers Area", "Cianda",
        ],
        "Thika (Kiambu side)": [
            "Mangu", "Gatundu", "Githunguri",
        ],
    },
    "Machakos": {
        "Machakos Town": [
            "Machakos CBD", "Machakos Estate", "Majengo", "Kalama", "Mulundi",
        ],
        "Athi River (Mavoko)": [
            "Athi River", "Mlolongo", "Syokimau", "Katani", "Kinanie",
        ],
        "Kangundo & Tala": [
            "Kangundo", "Tala", "Matuu",
        ],
    },
    "Kajiado": {
        "Ngong": [
            "Ngong Town", "Kibiko", "Rimpa", "Suswa",
        ],
        "Kitengela": [
            "Kitengela", "Isinya", "Kajiado Town",
        ],
        "Namanga": [
            "Namanga Town",
        ],
        "Magadi": [
            "Magadi Town",
        ],
    },
    "Murang'a": {
        "Murang'a Town": [
            "Murang'a CBD", "Kenol", "Maragua",
        ],
        "Kangema & Mathioya": [
            "Kangema", "Mathioya",
        ],
        "Kandara": [
            "Kandara", "Gaichanjiru",
        ],
    },
    "Nyeri": {
        "Nyeri Town": [
            "Nyeri CBD", "Karatina", "Othaya", "Mukurweini", "Ruring'u",
        ],
        "Nanyuki (Laikipia border)": [
            "Nanyuki Town",
        ],
    },
    "Kirinyaga": {
        "Kerugoya & Kutus": [
            "Kerugoya", "Kutus", "Sagana", "Wanguru",
        ],
        "Mwea": [
            "Mwea Town", "Tebere",
        ],
    },
    "Embu": {
        "Embu Town": [
            "Embu CBD", "Kirimari", "Kagaari", "Runyenjes",
        ],
        "Mbeere": [
            "Siakago", "Ishiara",
        ],
    },
    "Meru": {
        "Meru Town": [
            "Meru CBD", "Makutano", "Nkubu", "Maua", "Timau", "Laare",
        ],
        "Tharaka Nithi border": [
            "Chuka", "Kathwana",
        ],
    },
    "Tharaka Nithi": {
        "Chuka": [
            "Chuka Town", "Marimanti",
        ],
        "Tharaka": [
            "Gatunga",
        ],
    },
    "Isiolo": {
        "Isiolo Town": [
            "Isiolo CBD", "Bulla Pesa", "Wabera",
        ],
    },
    "Marsabit": {
        "Marsabit Town": [
            "Marsabit CBD", "Moyale", "Laisamis",
        ],
    },
    "Samburu": {
        "Maralal": [
            "Maralal Town", "Baragoi",
        ],
    },
    "Laikipia": {
        "Nanyuki": [
            "Nanyuki Town", "Marura", "Rumuruti", "Doldol", "Ol Kalou border",
        ],
    },
    "Nyandarua": {
        "Ol Kalou": [
            "Ol Kalou Town", "Engineer", "Ndaragwa", "Njabini",
        ],
    },
    "Kericho": {
        "Kericho Town": [
            "Kericho CBD", "Londiani", "Kipkelion", "Litein",
        ],
    },
    "Bomet": {
        "Bomet Town": [
            "Bomet CBD", "Sotik", "Longisa",
        ],
    },
    "Narok": {
        "Narok Town": [
            "Narok CBD", "Kilgoris", "Suswa",
        ],
    },
    "Trans Nzoia": {
        "Kitale": [
            "Kitale CBD", "Kiminini", "Endebess", "Saboti", "Matisi",
        ],
    },
    "Uasin Gishu": {
        "Eldoret": [
            "Eldoret CBD", "Huruma", "Langas", "Kapsabet Road",
            "Eldoret West", "Pioneer", "Munyaka", "Elgon View",
            "Annex", "Kimumu",
        ],
        "Turbo": [
            "Turbo Town",
        ],
    },
    "Elgeyo Marakwet": {
        "Iten & Eldoret border": [
            "Iten Town", "Chepkorio", "Kapsowar",
        ],
    },
    "Nandi": {
        "Kapsabet": [
            "Kapsabet Town", "Nandi Hills", "Kobujoi",
        ],
    },
    "Baringo": {
        "Kabarnet": [
            "Kabarnet Town", "Eldama Ravine", "Marigat", "Mogotio",
        ],
    },
    "West Pokot": {
        "Kapenguria": [
            "Kapenguria Town", "Makutano",
        ],
    },
    "Turkana": {
        "Lodwar": [
            "Lodwar Town", "Kakuma", "Lokichoggio",
        ],
    },
    "Bungoma": {
        "Bungoma Town": [
            "Bungoma CBD", "Webuye", "Chwele", "Kimilili", "Tongaren",
        ],
    },
    "Kakamega": {
        "Kakamega Town": [
            "Kakamega CBD", "Mumias", "Butere", "Shinyalu", "Lurambi",
        ],
    },
    "Vihiga": {
        "Vihiga": [
            "Vihiga Town", "Mbale", "Hamisi", "Majengo Vihiga",
        ],
    },
    "Siaya": {
        "Siaya Town": [
            "Siaya CBD", "Bondo", "Ugunja", "Ukwala", "Ndori", "Yala",
        ],
    },
    "Homa Bay": {
        "Homa Bay Town": [
            "Homa Bay CBD", "Kendu Bay", "Mbita", "Ndhiwa", "Oyugis",
        ],
    },
    "Migori": {
        "Migori Town": [
            "Migori CBD", "Awendo", "Rongo", "Uriri", "Isebania",
        ],
    },
    "Kisii": {
        "Kisii Town": [
            "Kisii CBD", "Ogembo", "Suneka", "Keroka", "Nyamache", "Manga",
        ],
    },
    "Nyamira": {
        "Nyamira Town": [
            "Nyamira CBD", "Keroka", "Nyansiongo",
        ],
    },
    "Kilifi": {
        "Kilifi Town": [
            "Kilifi CBD", "Malindi", "Watamu", "Mtwapa", "Rabai",
        ],
        "Malindi": [
            "Malindi Town", "Watamu", "Gede",
        ],
    },
    "Kwale": {
        "Kwale Town": [
            "Kwale CBD", "Diani", "Ukunda", "Msambweni",
            "Shimba Hills", "Lungalunga",
        ],
    },
    "Taita Taveta": {
        "Voi": [
            "Voi Town", "Wundanyi", "Mwatate", "Taveta",
        ],
    },
    "Tana River": {
        "Hola": [
            "Hola Town", "Garsen", "Bura",
        ],
    },
    "Lamu": {
        "Lamu Town": [
            "Lamu Island", "Shela", "Mokowe", "Mpeketoni", "Witu",
        ],
    },
    "Garissa": {
        "Garissa Town": [
            "Garissa CBD", "Dadaab", "Hulugho",
        ],
    },
    "Wajir": {
        "Wajir Town": [
            "Wajir CBD", "Habaswein", "Bute",
        ],
    },
    "Mandera": {
        "Mandera Town": [
            "Mandera CBD", "Elwak", "Rhamu",
        ],
    },
    "Makueni": {
        "Wote": [
            "Wote Town", "Sultan Hamud", "Emali", "Kibwezi", "Makindu",
        ],
    },
    "Kitui": {
        "Kitui Town": [
            "Kitui CBD", "Mwingi", "Mutomo", "Zombe", "Tseikuru",
        ],
    },
    "Busia": {
        "Busia Town": [
            "Busia CBD", "Malaba", "Butula", "Nambale", "Funyula",
        ],
    },
}


class Command(BaseCommand):
    help = "Seed the database with all 47 Kenyan counties, towns, and estates"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Kenya location data — all 47 counties...")

        county_count = town_count = estate_count = 0

        for county_name, towns in DATA.items():
            county, created = County.objects.get_or_create(name=county_name)
            if created:
                county_count += 1

            for town_name, estates in towns.items():
                town, created = Town.objects.get_or_create(
                    county=county, name=town_name
                )
                if created:
                    town_count += 1

                for estate_name in estates:
                    _, created = Estate.objects.get_or_create(
                        town=town, name=estate_name
                    )
                    if created:
                        estate_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created: {county_count} counties, "
            f"{town_count} towns, {estate_count} estates/areas."
        ))
