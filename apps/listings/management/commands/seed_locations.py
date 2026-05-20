"""
Management command: seed_locations
Populates Kenyan counties, towns, and Nairobi estates.
Run: python manage.py seed_locations
"""

from django.core.management.base import BaseCommand
from apps.listings.models import County, Town, Estate


NAIROBI_ESTATES = [
    # Westlands & surrounds
    "Westlands", "Parklands", "Highridge", "Lower Kabete", "Kangemi",
    # Nairobi South
    "Nairobi West", "South B", "South C", "Langata", "Karen",
    # Eastlands
    "Umoja", "Donholm", "Komarock", "Embakasi", "Utawala", "Pipeline",
    "Buruburu", "Kayole", "Njiru", "Ruai",
    # Nairobi North / CBD adjacent
    "Ngara", "Pangani", "Mlango Kubwa", "Huruma", "Mathare", "Roysambu",
    "Kasarani", "Mwiki", "Clay City", "Githurai",
    # Satellite towns
    "Rongai", "Ngong", "Ruaka", "Limuru", "Kikuyu", "Banana",
    "Kitengela", "Athi River", "Mlolongo", "Syokimau",
    # Thika Road
    "Kahawa West", "Kahawa Wendani", "Garden Estate", "Allsopps",
    "Muthaiga North", "Ruaraka", "Zimmerman",
    # Industrial area / CBD
    "Industrial Area", "Upper Hill", "Kilimani", "Lavington",
    "Valley Arcade", "Adams Arcade", "Woodley",
]


DATA = {
    "Nairobi": {
        "Nairobi": NAIROBI_ESTATES,
        "Ruiru": ["Ruiru Town", "Kamakis", "Eastern Bypass"],
        "Thika": ["Thika Town", "Makongeni", "Gatuanyaga"],
    },
    "Kiambu": {
        "Kiambu Town": ["Kiambu Town Centre", "Ndumberi"],
        "Kikuyu": ["Kikuyu Town", "Kinoo", "Kawangware"],
        "Limuru": ["Limuru Town", "Tigoni"],
    },
    "Mombasa": {
        "Mombasa": [
            "Nyali", "Bamburi", "Shanzu", "Tudor", "Likoni", "Changamwe",
            "Kisauni", "Mtwapa", "Mikindani",
        ],
    },
    "Nakuru": {
        "Nakuru Town": ["Nakuru Town", "Section 58", "Milimani", "London"],
    },
    "Kisumu": {
        "Kisumu Town": ["Kisumu CBD", "Milimani", "Lolwe", "Nyamasaria", "Mamboleo"],
    },
}


class Command(BaseCommand):
    help = "Seed the database with Kenyan counties, towns, and estates"

    def handle(self, *args, **options):
        self.stdout.write("Seeding location data...")

        county_count = town_count = estate_count = 0

        for county_name, towns in DATA.items():
            county, created = County.objects.get_or_create(name=county_name)
            if created:
                county_count += 1

            for town_name, estates in towns.items():
                town, created = Town.objects.get_or_create(county=county, name=town_name)
                if created:
                    town_count += 1

                for estate_name in estates:
                    _, created = Estate.objects.get_or_create(town=town, name=estate_name)
                    if created:
                        estate_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done! Created: {county_count} counties, {town_count} towns, {estate_count} estates."
        ))
