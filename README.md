# tobis
API for public transit &amp; shuttles in Morocco 🇲🇦

## Supported Providers

### Live Datasets (real-time tracking & pricing)
| Provider | Coverage | Type |
| :--- | :--- | :--- |
| **ONCF** | Trains | National |
| **CTM** | Coaches | National |
| **Supratours** | Coaches and bus relays | National |
| **Markoub.ma** | 50+ regional companies | National |
| **ALSA** | Agadir, Marrakech, Rabat, Khouribga | Urban |
| **Casabus** | Casablanca (ALSA) | Urban |

### Static Data (estimated schedules & pricing)
| Provider | Coverage | Type |
| :--- | :--- | :--- |
| **Laayoune Bus** | Laayoune | Urban |
| **SAPST Taghazout Bay** | Taghazout Shuttle | Regional |
| **Al Akhawayn University** | Ifrane Shuttles | Regional |

## Getting Started
This API is built with Python and FastAPI.

1. clone the repository
```bash
git clone https://github.com/elmkl/tobis.git
cd tobis
```

2. install requirements
```bash
pip install -r requirements.txt
```

3. run server
```bash
uvicorn main:app --reload
```

## Example
Search for a national trip (Casa-Tanger):
GET /national/search?from=casablanca&to=tanger&travel_date=2026-05-06

Track an urban route (Agadir Airport Shuttle):
GET /urban/alsa/agadir/track/L-AE


This project is endorsed by none of these transit companies.