import json
import sys
from pathlib import Path

# Adiciona a pasta "src" ao sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from chat.utils.mongo_manage import MongoDBManager
from manager import BusinessPlanManager

dic = {
    "session_id": "3b3513af-0750-47fa-a679-5366d96adec5",
    "business_id": "0010",
    "input": "Quais arquivos estão na base?",
    "response": "Na base de conhecimento, há um arquivo chamado \"Cittadinanza italiana iure sanguinis\" que é um arquivo no formato PDF. Este arquivo contém informações sobre como obter a cidadania italiana por descendência (iure sanguinis), os requisitos necessários, os documentos a serem apresentados, o processo de naturalização ou falta dela, entre outros detalhes. Caso tenha interesse em mais informações sobre esse arquivo específico, por favor me avise!",
    "metadata": {
        "user_id": "user_123"
    },
    "tempo_execucao_s": 9.55,
    "status": "success",
    "tool": "AnswerGeneration",
    "tool_output": "{'tool': 'AnswerGeneration', 'response': \"{'file_name': 'Cittadinanza italiana iure sanguinis',  'extention': 'pdf',  'file_content': 'Cittadinanza italiana iure sanguinis\\\\n1\\\\nCittadinanza italiana iure \\\\nsanguinis\\\\nIs Active\\\\nTipo\\\\nStatus\\\\nNot started\\\\nCosa devo avere per prendere la cittadinanza italiana \\\\nuna volta che ho fatto l\\\\'albero genealogico fino al \\\\nmio trisavo che è nato in Italia?\\\\nPer ottenere la cittadinanza italiana attraverso la discendenza (iure sanguinis), \\\\nbisogna soddisfare una serie di requisiti. Ecco cosa devi fare una volta che hai \\\\ngià ricostruito l\\\\'albero genealogico fino al tuo trisavolo nato in Italia:\\\\n1. Verifica della continuità della cittadinanza:\\\\nDevi dimostrare che la cittadinanza italiana è stata mantenuta senza \\\\ninterruzioni da parte dei tuoi antenati fino a te. Ciò significa che i tuoi \\\\nantenati non devono aver perso la cittadinanza italiana per \\\\nnaturalizzazione in un altro paese o per altre cause.\\\\nLa cittadinanza si trasmette da una generazione all\\\\'altra, quindi devi\\n\\nitaliano dove è nato.\\\\nCertificato di matrimonio (se applicabile): Se il matrimonio è avvenuto in \\\\nItalia o in un altro paese, dovrai fornire il documento corrispondente.\\\\nCertificato di morte (se applicabile): Utile per completare il quadro \\\\ngenealogico, anche se non sempre richiesto.\\\\n2. Documenti di tutti i discendenti diretti (fino a te)\\\\nPer ciascun antenato della linea diretta (bisavolo, nonno, genitore e te stesso), \\\\ndevi fornire:\\\\nCertificati di nascita: Devono dimostrare il legame diretto con l’antenato \\\\nitaliano.\\\\nCertificati di matrimonio (se applicabile): Necessari per dimostrare la \\\\ntrasmissione del cognome e della discendenza.\\\\nCertificati di morte (se applicabile): Non sempre richiesti, ma possono \\\\nessere utili per evitare discrepanze.\\\\n3. Prova della naturalizzazione o mancata naturalizzazione\\\\nDevi fornire un certificato che dimostri che il tuo trisavolo italiano:\\\\nNon si è mai naturalizzato cittadino brasiliano oppure\\\\nSe si è naturalizzato, lo ha fatto dopo la\\n\\no mancata naturalizzazione\\\\nDevi fornire un certificato che dimostri che il tuo trisavolo italiano:\\\\nNon si è mai naturalizzato cittadino brasiliano oppure\\\\nSe si è naturalizzato, lo ha fatto dopo la nascita del suo discendente \\\\ndiretto (ad esempio, il tuo bisavolo).\\\\nQuesta prova è spesso ottenuta tramite un documento ufficiale del \\\\nBrasile (Certidão Negativa de Naturalização - CNN) o simili.\\\\n4. Documenti personali\\\\nPer completare la domanda, serviranno anche:\\\\nLa tua certidão de nascimento e, se applicabile, il certificato di matrimonio.\\\\nDocumenti di identità validi.\\\\nNota importante\\\\nCittadinanza italiana iure sanguinis\\\\n6\\\\nLa cittadinanza italiana non viene trasmessa attraverso donne se la nascita \\\\ndel discendente è avvenuta prima del 1° gennaio 1948. Ad esempio, se la \\\\ntua linea genealogica passa per una donna e il figlio di questa donna è nato \\\\nprima di questa data, il diritto potrebbe non essere riconosciuto \\\\nautomaticamente. In tal caso, sarebbe necessario un ricorso\\n\\no alla \\\\nQuestura) per richiedere il passaporto.\\\\n2. Porta con te una fototessera, un documento d’identità e il certificato di \\\\ncittadinanza rilasciato.\\\\nMio trisavo è nato in Italia e venuto al brasile, se ho \\\\ntutti i suoi documenti è già\\\\' abbastanza per la \\\\ncittadinanza oppure devo avere anche i documenti \\\\ndei suoi genitori?\\\\nPer ottenere la cittadinanza italiana iure sanguinis, non è necessario avere i \\\\ndocumenti dei genitori del tuo trisavolo. È sufficiente dimostrare la tua \\\\ndiscendenza diretta dal trisavolo italiano, nato in Italia, fino a te. Quindi, i \\\\ndocumenti richiesti includono:\\\\n1. Documenti del tuo trisavolo italiano (antenato italiano)\\\\nCittadinanza italiana iure sanguinis\\\\n5\\\\nCertificato di nascita (estratto dell’atto di nascita): Deve essere richiesto \\\\npresso il Comune italiano dove è nato.\\\\nCertificato di matrimonio (se applicabile): Se il matrimonio è avvenuto in \\\\nItalia o in un altro paese, dovrai fornire il documento corrispondente.\\\\nCertificato di morte\\n\\nesserci un ostacolo.\\\\n5. Tempi e processo:\\\\nIl processo di riconoscimento della cittadinanza può richiedere vari mesi\\\\no anche anni, a seconda della complessità del caso e del carico di \\\\nlavoro del consolato o dell\\\\'ufficio del comune.\\\\nTi consiglio di contattare il consolato italiano competente per avere \\\\ninformazioni specifiche sui requisiti e i documenti necessari, poiché le \\\\nprocedure possono variare in base alla tua situazione e alla localizzazione.\\\\nSe trovo questi documenti cosa bisogna fare dopo?\\\\nUna volta raccolti tutti i documenti necessari, ecco i passi successivi da seguire \\\\nper ottenere la cittadinanza italiana iure sanguinis:\\\\n1. Verifica della completezza dei documenti\\\\nAssicurati che tutti i documenti siano in ordine cronologico e collegati tra \\\\nloro (ad esempio, che i certificati di nascita, matrimonio e morte dimostrino \\\\nchiaramente la discendenza diretta tra te e il tuo trisavolo italiano).\\\\nCittadinanza italiana iure sanguinis\\\\n3\\\\nVerifica che non ci siano\"}",
    "tokens_estimados": {
        "input": {
            "parts": {
                "system": {
                    "caracters": 780,
                    "tokens_estimated": 166
                },
                "chat_history": {
                    "caracters": 474,
                    "tokens_estimated": 94
                },
                "tools": {
                    "caracters": 2677,
                    "tokens_estimated": 659
                },
                "tool_response": {
                    "caracters": 4989,
                    "tokens_estimated": 1303
                }
            },
            "combined": {
                "caracters": 8923,
                "tokens_estimated": 5
            }
        },
        "output": {
            "caracters": 444,
            "tokens_estimated": 5
        },
        "total": {
            "caracters": 9367,
            "tokens_estimated": 10
        },
        "timestamp": "2025-10-29 17:19:16"
    }
}

if __name__ == "__main__":
    BUSINESS_ID = "0010"
    MODEL = "gpt-4o-mini"
    dic = dic

    mongo = MongoDBManager()
    manager = BusinessPlanManager(BUSINESS_ID, MODEL, dic, mongo)
    resultado = manager.execute()

    print(json.dumps(resultado, indent=4, ensure_ascii=False))
