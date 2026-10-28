import os
import asyncio
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote_plus

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")


def construire_liens(recherche):
    q = quote_plus(recherche)
    return {
        "COMPARATEURS": {
            "Google Shopping (prix croissant)": "https://www.google.com/search?tbm=shop&q=" + q + "&tbs=p_ord:p",
            "Idealo": "https://www.idealo.fr/prechcat.html?q=" + q,
            "LeDenicheur": "https://www.ledenicheur.fr/search?search=" + q,
            "Kelkoo": "https://www.kelkoo.fr/search?query=" + q,
            "Shopzilla": "https://www.google.com/search?q=" + q + "+comparateur+prix",
        },
        "GRANDS MAGASINS": {
            "Amazon (prix croissant)": "https://www.amazon.fr/s?k=" + q + "&s=price-asc-rank",
            "Amazon Warehouse (occasion)": "https://www.amazon.fr/s?k=" + q + "&i=warehouse-deals&s=price-asc-rank",
            "Cdiscount": "https://www.cdiscount.com/search/10/" + q + ".html",
            "Fnac": "https://www.fnac.com/SearchResult/ResultList.aspx?Search=" + q,
            "Darty": "https://www.darty.com/nav/recherche?text=" + q,
            "Boulanger": "https://www.boulanger.com/resultats?tr=" + q,
            "AliExpress": "https://fr.aliexpress.com/wholesale?SearchText=" + q + "&SortType=price_asc",
            "Temu": "https://www.temu.com/fr/search_result.html?search_key=" + q,
            "Shein": "https://fr.shein.com/pdsearch/" + q + "/",
            "Rakuten": "https://fr.shopping.rakuten.com/search/" + q,
        },
        "MODE ET SPORT": {
            "Zalando": "https://www.zalando.fr/catalogue/?q=" + q + "&order=price_asc",
            "Nike": "https://www.nike.com/fr/w?q=" + q + "&vst=" + q,
            "Adidas": "https://www.adidas.fr/search?q=" + q + "&sort=price-low-to-high",
            "Decathlon": "https://www.decathlon.fr/search?Ntt=" + q,
            "Foot Locker": "https://www.footlocker.fr/fr/search?query=" + q,
            "Courir": "https://www.courir.com/fr/search?q=" + q,
            "JD Sports": "https://www.jdsports.fr/search/" + q + "/",
            "Veepee": "https://www.google.com/search?q=site:veepee.fr+" + q,
            "Sarenza": "https://www.sarenza.com/recherche?q=" + q,
            "ASOS": "https://www.asos.com/fr/search/?q=" + q + "&sort=price_asc",
            "Stockx": "https://stockx.com/search?s=" + q,
        },
        "OCCASION ET PARTICULIERS": {
            "Vinted (moins cher d'abord)": "https://www.vinted.fr/catalog?search_text=" + q + "&order=price_low_to_high",
            "Leboncoin (prix croissant)": "https://www.leboncoin.fr/recherche?text=" + q + "&sort=price&order=asc",
            "eBay (prix croissant)": "https://www.ebay.fr/sch/i.html?_nkw=" + q + "&_sop=15",
            "Facebook Marketplace": "https://www.facebook.com/marketplace/search/?query=" + q + "&sortBy=price_ascend",
            "Back Market (reconditionne)": "https://www.backmarket.fr/fr-fr/search?q=" + q,
            "Vestiaire Collective": "https://fr.vestiairecollective.com/search/?q=" + q,
            "Wallapop": "https://es.wallapop.com/app/search?keywords=" + q,
            "Troc.com": "https://www.google.com/search?q=site:troc.com+" + q,
        },
        "BONS PLANS ET PROMOS": {
            "Dealabs": "https://www.dealabs.com/search?q=" + q,
            "Groupes Facebook de bons plans": "https://www.google.com/search?q=site:facebook.com/groups+bons+plans+" + q,
            "Groupes WhatsApp de promos": "https://www.google.com/search?q=groupe+whatsapp+bons+plans+promos+" + q,
            "Groupes Telegram de promos": "https://www.google.com/search?q=site:t.me+bons+plans+promos+" + q,
            "Codes promo": "https://www.google.com/search?q=code+promo+" + q,
            "Promos et soldes": "https://www.google.com/search?q=" + q + "+promo+soldes",
            "Promodescuentos / Pepper": "https://www.pepper.com/search?q=" + q,
            "Reddit bons plans": "https://www.reddit.com/search/?q=bons+plans+" + q,
            "Ventes privees": "https://www.google.com/search?q=vente+privee+" + q,
        },
    }


class Ping(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Radar Promo OK")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def lancer_ping():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Ping).serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("COMMANDE START RECUE")

    if update.message is None:
        logger.warning("Aucun message reçu pour /start")
        return

    texte = (
        "Bienvenue sur Radar Promo !\n\n"
        "Je cherche pour toi les meilleurs prix et les bons plans.\n\n"
        "Exemple :\n"
        "/prix chaussures nike taille 42\n\n"
        "Je te donne les liens vers plus de 40 sites."
    )

    try:
        await update.message.reply_text(texte)
        logger.info("REPONSE START ENVOYEE")
    except Exception:
        logger.exception("ECHEC DE LA REPONSE START")
        raise


async def prix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Dis-moi ce que tu cherches. Exemple :\n/prix chaussures nike taille 42"
        )
        return

    recherche = " ".join(context.args)
    groupes = construire_liens(recherche)

    await update.message.reply_text("Resultats pour : " + recherche)

    for titre, liens in groupes.items():
        message = titre + "\n\n"
        for nom, lien in liens.items():
            message += "- " + nom + "\n" + lien + "\n\n"
        await update.message.reply_text(message, disable_web_page_preview=True)


async def erreur(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erreur : %s", context.error)


def main() -> None:
    if not TOKEN:
        raise RuntimeError("La variable TELEGRAM_TOKEN est manquante. Ajoute-la dans les parametres de Render.")

    threading.Thread(target=lancer_ping, daemon=True).start()
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prix", prix))
    app.add_error_handler(erreur)

    logger.info("Radar Promo demarre...")
    app.run_polling()


if __name__ == "__main__":
    main()
