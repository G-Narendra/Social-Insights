"""
Script to generate the 100-sample hand-labeled evaluation dataset.
Spans diverse domains (automotive, technology, customer service) across
all 3 sentiments (positive, neutral, negative) and all 8 topics.
"""

import json
from pathlib import Path

DATASET_PATH = Path(__file__).parent / "labelled_sample.jsonl"

SAMPLES = [
    # --- POSITIVE (35 samples) ---
    # product (5)
    {
        "text": "The new 2026 Camry redesign looks so sleek and aggressive in person.",
        "sentiment": "positive",
        "topic": "product",
    },
    {
        "text": "Toyota GR86 has one of the best chassis and manual transmissions in the market.",
        "sentiment": "positive",
        "topic": "product",
    },
    {
        "text": "The styling on the new Land Cruiser is perfection, retro yet modern.",
        "sentiment": "positive",
        "topic": "product",
    },
    {
        "text": "The interior space in the Grand Highlander easily fits our family of six.",
        "sentiment": "positive",
        "topic": "product",
    },
    {
        "text": "In love with the twin-turbo V6 setup in the new Tundra, tons of pulling power.",
        "sentiment": "positive",
        "topic": "product",
    },
    # quality (6)
    {
        "text": "Hit 250,000 miles on my Corolla with only routine oil changes and brake pads.",
        "sentiment": "positive",
        "topic": "quality",
    },
    {
        "text": "Toyota reliability is unmatched, 10 years without a single unexpected breakdown.",
        "sentiment": "positive",
        "topic": "quality",
    },
    {
        "text": "Solid build quality, zero rattles or creaks inside the cabin after 3 years.",
        "sentiment": "positive",
        "topic": "quality",
    },
    {
        "text": "The engine bay is engineered for ease of maintenance, built to last forever.",
        "sentiment": "positive",
        "topic": "quality",
    },
    {
        "text": "Consumer Reports ranked Toyota top tier for long-term vehicle durability again.",
        "sentiment": "positive",
        "topic": "quality",
    },
    {
        "text": "Passed the state vehicle inspection with flying colors on my 2012 Prius.",
        "sentiment": "positive",
        "topic": "quality",
    },
    # features (6)
    {
        "text": "Getting 52 MPG on my daily commute in the Prius Prime, fuel efficiency is incredible.",
        "sentiment": "positive",
        "topic": "features",
    },
    {
        "text": "Wireless Apple CarPlay connects instantly every time I start the car.",
        "sentiment": "positive",
        "topic": "features",
    },
    {
        "text": "Dynamic radar cruise control and lane tracing assist make highway road trips effortless.",
        "sentiment": "positive",
        "topic": "features",
    },
    {
        "text": "The JBL premium audio sound system in the Crown Signia sounds phenomenal.",
        "sentiment": "positive",
        "topic": "features",
    },
    {
        "text": "Heated and ventilated seats warm up within thirty seconds in freezing winter.",
        "sentiment": "positive",
        "topic": "features",
    },
    {
        "text": "The 360-degree panoramic view monitor makes parking this massive SUV a breeze.",
        "sentiment": "positive",
        "topic": "features",
    },
    # pricing (5)
    {
        "text": "Found a dealership selling the RAV4 hybrid at straight MSRP with zero dealer markup.",
        "sentiment": "positive",
        "topic": "pricing",
    },
    {
        "text": "Toyota 1.9% financing deal for 60 months was impossible to beat this month.",
        "sentiment": "positive",
        "topic": "pricing",
    },
    {
        "text": "Total cost of ownership on these hybrid models is the lowest in the entire industry.",
        "sentiment": "positive",
        "topic": "pricing",
    },
    {
        "text": "Resale value on Tacoma trucks is unbelievable, sold mine for 85% of what I paid.",
        "sentiment": "positive",
        "topic": "pricing",
    },
    {
        "text": "Got a great rebate on the bZ4X electric vehicle lease deal this weekend.",
        "sentiment": "positive",
        "topic": "pricing",
    },
    # customer_service (5)
    {
        "text": "The service department finished my 10k mile maintenance check in under 45 minutes.",
        "sentiment": "positive",
        "topic": "customer_service",
    },
    {
        "text": "My local dealer provided a complimentary loaner vehicle while doing recall work.",
        "sentiment": "positive",
        "topic": "customer_service",
    },
    {
        "text": "Our sales consultant was friendly, honest, and didn't pressure us on add-on packages.",
        "sentiment": "positive",
        "topic": "customer_service",
    },
    {
        "text": "Warranty claim for a minor sensor issue was approved without any hassle.",
        "sentiment": "positive",
        "topic": "customer_service",
    },
    {
        "text": "Quick response from customer care when my app account needed resetting.",
        "sentiment": "positive",
        "topic": "customer_service",
    },
    # competitors (4)
    {
        "text": "Test drove Honda CR-V and Toyota RAV4; picked the RAV4 for superior hybrid powertrain.",
        "sentiment": "positive",
        "topic": "competitors",
    },
    {
        "text": "Traded in my troubled Ford F-150 for a Tundra and haven't looked back once.",
        "sentiment": "positive",
        "topic": "competitors",
    },
    {
        "text": "Toyota builds a much more durable suspension than Subaru for rocky trails.",
        "sentiment": "positive",
        "topic": "competitors",
    },
    {
        "text": "Tesla build quality pales in comparison to the tight tolerances of Toyota factories.",
        "sentiment": "positive",
        "topic": "competitors",
    },
    # other (4)
    {
        "text": "Toyota announced a $1.3B investment in their Kentucky plant for US manufacturing.",
        "sentiment": "positive",
        "topic": "other",
    },
    {
        "text": "Chairman Akio Toyoda receives lifetime automotive achievement award.",
        "sentiment": "positive",
        "topic": "other",
    },
    {
        "text": "Toyota Gazoo Racing clinches another double podium victory at 24 Hours of Le Mans.",
        "sentiment": "positive",
        "topic": "other",
    },
    {
        "text": "Toyota stock rises 3% after beating Wall Street consensus quarterly earnings.",
        "sentiment": "positive",
        "topic": "other",
    },
    # --- NEGATIVE (35 samples) ---
    # pricing (7)
    {
        "text": "Dealership markup of $10,000 over MSRP on the Sienna minivan is pure extortion.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    {
        "text": "Overpriced subscription fees just to use the remote start button on my physical key fob.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    {
        "text": "Financing interest rates from Toyota Financial are absurdly high right now.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    {
        "text": "Dealer added $2,500 of useless mandatory accessories like nitrogen in tires.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    {
        "text": "The monthly payment on a base model Tacoma is now over $650, completely unaffordable.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    {
        "text": "Replacement parts for the radar cruise sensor cost $1,800, crazy expensive repair.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    {
        "text": "Dealers are price gouging enthusiastic buyers on the new Land Cruiser.",
        "sentiment": "negative",
        "topic": "pricing",
    },
    # quality (7)
    {
        "text": "Major recall announced for engine debris causing sudden loss of motive power on highways.",
        "sentiment": "negative",
        "topic": "quality",
    },
    {
        "text": "My transmission is slipping and jerking between second and third gear at only 15,000 miles.",
        "sentiment": "negative",
        "topic": "quality",
    },
    {
        "text": "Peeling white paint defect on the roof and hood that Toyota refuses to cover.",
        "sentiment": "negative",
        "topic": "quality",
    },
    {
        "text": "Annoying dashboard and door panel rattles driving me crazy on highway trips.",
        "sentiment": "negative",
        "topic": "quality",
    },
    {
        "text": "The high voltage hybrid cable corroded underneath the car in winter salt states.",
        "sentiment": "negative",
        "topic": "quality",
    },
    {
        "text": "Check engine light came on three times in the first two months of ownership.",
        "sentiment": "negative",
        "topic": "quality",
    },
    {
        "text": "Water leaking through the panoramic sunroof into the headliner after light rain.",
        "sentiment": "negative",
        "topic": "quality",
    },
    # complaints (7)
    {
        "text": "I deeply regret buying this car, total lemon and dealer refuses a buyback.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    {
        "text": "Horrible experience, broken down three times in six months on the interstate.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    {
        "text": "Joined the class action lawsuit over unresolved engine failures and fire risks.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    {
        "text": "Furious customer here, car spent 45 days at the shop with zero resolution.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    {
        "text": "Worst purchase decision I have ever made, avoid this model at all costs.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    {
        "text": "Unacceptable negligence leaving customers stranded without loaner vehicles.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    {
        "text": "This brand has completely lost its way, absolute disaster of a vehicle.",
        "sentiment": "negative",
        "topic": "complaints",
    },
    # customer_service (6)
    {
        "text": "Dealership service department kept my car for two weeks without even looking at it.",
        "sentiment": "negative",
        "topic": "customer_service",
    },
    {
        "text": "Rude and dismissive service advisor refused to honor the factory powertrain warranty.",
        "sentiment": "negative",
        "topic": "customer_service",
    },
    {
        "text": "Customer support hotline kept me on hold for 2 hours and then hung up.",
        "sentiment": "negative",
        "topic": "customer_service",
    },
    {
        "text": "Salesman lied about vehicle delivery dates, pushed delivery back four times.",
        "sentiment": "negative",
        "topic": "customer_service",
    },
    {
        "text": "Dealer scratched my front bumper during an oil change and claimed it was pre-existing.",
        "sentiment": "negative",
        "topic": "customer_service",
    },
    {
        "text": "Unhelpful corporate care representative told me to deal with the franchise directly.",
        "sentiment": "negative",
        "topic": "customer_service",
    },
    # product (4)
    {
        "text": "The rear seat legroom is way too cramped for average height adults.",
        "sentiment": "negative",
        "topic": "product",
    },
    {
        "text": "Cheap hard plastics everywhere on the door trim and center console look awful.",
        "sentiment": "negative",
        "topic": "product",
    },
    {
        "text": "The styling of the front grille looks like an angry vacuum cleaner, hideous.",
        "sentiment": "negative",
        "topic": "product",
    },
    {
        "text": "The trunk opening is oddly narrow, cannot fit a standard stroller easily.",
        "sentiment": "negative",
        "topic": "product",
    },
    # competitors (4)
    {
        "text": "Hyundai offers a 10 year warranty while Toyota only provides an inferior 5 year warranty.",
        "sentiment": "negative",
        "topic": "competitors",
    },
    {
        "text": "Honda interior ergonomics and touchscreen responsiveness blow Toyota away.",
        "sentiment": "negative",
        "topic": "competitors",
    },
    {
        "text": "Ford F-150 hybrid generator power is vastly superior to the Tundra hybrid setup.",
        "sentiment": "negative",
        "topic": "competitors",
    },
    {
        "text": "Kia EV9 makes Toyota electric vehicle offerings look ten years outdated.",
        "sentiment": "negative",
        "topic": "competitors",
    },
    # --- NEUTRAL (30 samples) ---
    # product (5)
    {
        "text": "Toyota will reveal the next generation 2027 RAV4 at the Los Angeles Auto Show.",
        "sentiment": "neutral",
        "topic": "product",
    },
    {
        "text": "The 2026 Camry is available exclusively with a 2.5-liter four-cylinder hybrid powertrain.",
        "sentiment": "neutral",
        "topic": "product",
    },
    {
        "text": "Ground clearance on the base trim measures 8.2 inches compared to 8.6 on TRD Off-Road.",
        "sentiment": "neutral",
        "topic": "product",
    },
    {
        "text": "Available exterior color options include Blueprint, Wind Chill Pearl, and Underground gray.",
        "sentiment": "neutral",
        "topic": "product",
    },
    {
        "text": "The vehicle measures 196 inches in total length with a 112 inch wheelbase.",
        "sentiment": "neutral",
        "topic": "product",
    },
    # pricing (5)
    {
        "text": "Manufacturer suggested retail pricing for the base LE starts at $28,400 before destination.",
        "sentiment": "neutral",
        "topic": "pricing",
    },
    {
        "text": "Destination and handling charge adds $1,095 to the total window sticker price.",
        "sentiment": "neutral",
        "topic": "pricing",
    },
    {
        "text": "Estimated annual insurance cost for this model averages approximately $1,650.",
        "sentiment": "neutral",
        "topic": "pricing",
    },
    {
        "text": "Comparing lease payments between 36-month and 39-month financing terms.",
        "sentiment": "neutral",
        "topic": "pricing",
    },
    {
        "text": "State sales tax and title registration fees vary based on purchasing county.",
        "sentiment": "neutral",
        "topic": "pricing",
    },
    # features (5)
    {
        "text": "The center console features two USB-C charging ports and one 12-volt accessory outlet.",
        "sentiment": "neutral",
        "topic": "features",
    },
    {
        "text": "Toyota Safety Sense 3.0 includes pedestrian detection and proactive driving assist.",
        "sentiment": "neutral",
        "topic": "features",
    },
    {
        "text": "EPA estimated fuel economy rating is 44 MPG city and 43 MPG highway.",
        "sentiment": "neutral",
        "topic": "features",
    },
    {
        "text": "Supports over-the-air software updates through an integrated 4G LTE cellular connection.",
        "sentiment": "neutral",
        "topic": "features",
    },
    {
        "text": "The hybrid battery pack is positioned under the rear seats to preserve cargo area.",
        "sentiment": "neutral",
        "topic": "features",
    },
    # customer_service (4)
    {
        "text": "Scheduled my scheduled 20,000 mile tire rotation and multi-point inspection for Tuesday.",
        "sentiment": "neutral",
        "topic": "customer_service",
    },
    {
        "text": "Service center hours of operation are 7:00 AM to 6:00 PM Monday through Friday.",
        "sentiment": "neutral",
        "topic": "customer_service",
    },
    {
        "text": "Toyota Care covers complimentary factory scheduled maintenance for 2 years or 25,000 miles.",
        "sentiment": "neutral",
        "topic": "customer_service",
    },
    {
        "text": "Received an email reminder from the dealership regarding the upcoming service interval.",
        "sentiment": "neutral",
        "topic": "customer_service",
    },
    # competitors (4)
    {
        "text": "Comparing dimension specifications between Toyota Highlander and Honda Pilot.",
        "sentiment": "neutral",
        "topic": "competitors",
    },
    {
        "text": "Both Toyota and Nissan offer compact crossovers in the $30,000 price category.",
        "sentiment": "neutral",
        "topic": "competitors",
    },
    {
        "text": "Market share data shows Toyota and General Motors competing for top US sales spot.",
        "sentiment": "neutral",
        "topic": "competitors",
    },
    {
        "text": "Examining battery pack capacities across Toyota, Hyundai, and Volkswagen EVs.",
        "sentiment": "neutral",
        "topic": "competitors",
    },
    # quality (3)
    {
        "text": "National Highway Traffic Safety Administration published a technical service bulletin.",
        "sentiment": "neutral",
        "topic": "quality",
    },
    {
        "text": "Standard factory powertrain warranty coverage spans 5 years or 60,000 miles.",
        "sentiment": "neutral",
        "topic": "quality",
    },
    {
        "text": "Routine oil change interval recommended by the owner's manual is every 10,000 miles.",
        "sentiment": "neutral",
        "topic": "quality",
    },
    # other (4)
    {
        "text": "Toyota Motor Corporation will release its third-quarter financial results on February 6.",
        "sentiment": "neutral",
        "topic": "other",
    },
    {
        "text": "The company operates major assembly manufacturing facilities in Georgetown, Kentucky.",
        "sentiment": "neutral",
        "topic": "other",
    },
    {
        "text": "Toyota announced executive leadership changes in its North American research division.",
        "sentiment": "neutral",
        "topic": "other",
    },
    {
        "text": "Patent filing describes new hydrogen fuel cell storage tank architecture.",
        "sentiment": "neutral",
        "topic": "other",
    },
]


def main():
    assert len(SAMPLES) == 100, f"Expected exactly 100 samples, got {len(SAMPLES)}"
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATASET_PATH, "w", encoding="utf-8") as f:
        for item in SAMPLES:
            f.write(json.dumps(item) + "\n")
    print(f"Generated {len(SAMPLES)} hand-labelled evaluation samples at {DATASET_PATH}")


if __name__ == "__main__":
    main()
