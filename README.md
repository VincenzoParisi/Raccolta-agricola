Questo progetto implementa un modello di ottimizzazione per la pianificazione della raccolta agricola, con l’obiettivo di individuare la combinazione più efficiente di operatori manuali e meccanizzati, interni ed esterni, necessaria per completare la raccolta entro vincoli di budget e tempo massimo.

Il sistema simula la produzione agricola su più colture, genera rese casuali per ettaro e valuta tutte le configurazioni possibili di forza lavoro, calcolando per ciascuna:

- il tempo totale di raccolta,

- il costo complessivo,

- la produzione ottenibile,

- la distinzione tra operatori interni ed esterni,

- i costi fissi e variabili associati ai macchinari.

Il programma restituisce tre soluzioni principali:

- Soluzione più veloce con soli operatori interni

- Soluzione più economica con soli operatori interni

- Soluzione con operatori esterni, qualora questi permettano un miglioramento in termini di costo o tempo
