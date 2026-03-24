import random
import math

# ============================================================
# COSTANTI
# ============================================================

RESA_MANUALE = 0.50		# tonnellate / ora prodotte da un operatore manuale
RESA_MECC = 2.0			# tonnellate /ora prodotte da un operatore interno meccanizzato

SAL_MAN_INT = 8.0		# salario orario degli operatori manuali interni
SAL_MECC_INT = 12.0		# salario orario degli operatori meccanizzati interni 
SAL_MAN_EXT = 12.0		# salario orario degli operatori manuali esterni
SAL_MECC_EXT = 18.0		# salario orario degli operatori meccanizzati esterni

CARB_HA = 20.0			# costo carburante per ettaro per ogni macchina interna
MANUT_HA = 8.0			# costo manutenzione per ettaro per ogni macchina interna

MAX_MAN_INT = 10		# massimo numero di operatori manuali interni
MAX_MECC_INT = 10		# massimo numero di operatori meccanizzati interni
MAX_EXTRA = 20			# massimo numero di operatori esterni

MAX_MAN_TOT = MAX_MAN_INT + MAX_EXTRA
MAX_MECC_TOT = MAX_MECC_INT + MAX_EXTRA

AFFITTO_MECC_EXT = 40.0		# costo orario per ogni macchina esterna utilizzata

CROPS = {			# rese casuali per ettaro di ogni coltura (range min, range max)
    "Orzo": (20.0, 25.0),
    "Avena": (18.0, 25.0),
    "Frumento": (25.0, 30.0),
}

# ============================================================
# FUNZIONI DI SUPPORTO
# ============================================================

def ore_necessarie(ton, resa_oraria):
    return int(math.ceil(ton / resa_oraria - 1e-12))

def costi_fissi(ettari, num_meccanizzati):
    interni = min(num_meccanizzati, MAX_MECC_INT)
    return num_meccanizzati * CARB_HA * ettari + interni * MANUT_HA * ettari

def costo_orario(num_manuali, num_meccanizzati):
    man_int = min(num_manuali, MAX_MAN_INT)
    man_ext = max(0, num_manuali - MAX_MAN_INT)
    mec_int = min(num_meccanizzati, MAX_MECC_INT)
    mec_ext = max(0, num_meccanizzati - MAX_MECC_INT)

    return (
        man_int * SAL_MAN_INT +
        man_ext * SAL_MAN_EXT +
        mec_int * SAL_MECC_INT +
        mec_ext * SAL_MECC_EXT
    )

def costo_totale(num_manuali, num_meccanizzati, ore_manual, ore_mecc, ettari):
    base = costo_orario(num_manuali, num_meccanizzati) * max(ore_manual, ore_mecc)
    if num_meccanizzati > 0 and ore_mecc > 0:
        base += costi_fissi(ettari, num_meccanizzati)
        if num_meccanizzati > MAX_MECC_INT:
            base += (num_meccanizzati - MAX_MECC_INT) * AFFITTO_MECC_EXT * ore_mecc
    return base

# ============================================================
# CRITERI DI ORDINAMENTO 
# ============================================================

def criterio_velocita(soluzione):
    return (soluzione["ore_tot"], soluzione["cost"])

def criterio_costo(soluzione):
    return (soluzione["cost"], soluzione["ore_tot"])

# ============================================================
# RICERCA SOLUZIONI
# ============================================================

def trova_soluzione(target, budget, ettari, max_manuali, max_meccanizzati, max_ore, priorita):
    soluzioni = []
    limite_ore = max_ore

    for num_manuali in range(max_manuali + 1):
        for num_meccanizzati in range(max_meccanizzati + 1):
            if num_manuali == 0 and num_meccanizzati == 0:
                continue

            for ore_mecc in range(limite_ore + 1 if num_meccanizzati > 0 else 1):
                mecc_eff = num_meccanizzati if ore_mecc > 0 else 0
                ton_mecc = mecc_eff * RESA_MECC * ore_mecc
                restante = target - ton_mecc

                if restante <= 0:
                    ore_manual = 0
                    man_eff = 0
                else:
                    if num_manuali == 0:
                        continue
                    man_eff = num_manuali
                    ore_manual = ore_necessarie(restante, man_eff * RESA_MANUALE)
                    if ore_manual > limite_ore:
                        continue

                ore_tot = max(ore_manual, ore_mecc)
                if ore_tot > limite_ore:
                    continue

                costo = costo_totale(man_eff, mecc_eff, ore_manual, ore_mecc, ettari)
                if costo > budget:
                    continue

                potenziale = ton_mecc + man_eff * RESA_MANUALE * ore_manual
                if potenziale + 1e-12 < target:
                    continue

                soluzioni.append({
                    "num_manuali": man_eff,
                    "num_meccanizzati": mecc_eff,
                    "ore_manual": ore_manual,
                    "ore_mecc": ore_mecc,
                    "ore_tot": ore_tot,
                    "cost": costo
                })

    if not soluzioni:
        return None

    if priorita == "FAST":
        return min(soluzioni, key=criterio_velocita)
    else:
        return min(soluzioni, key=criterio_costo)

def trova_interne(target, budget, ettari, max_ore):
    vel = trova_soluzione(target, budget, ettari, MAX_MAN_INT, MAX_MECC_INT, max_ore, "FAST")
    eco = trova_soluzione(target, budget, ettari, MAX_MAN_INT, MAX_MECC_INT, max_ore, "CHEAP")
    return vel, eco

def trova_esterni(target, budget, ettari, vel, eco, max_ore):
    est = trova_soluzione(target, budget, ettari, MAX_MAN_TOT, MAX_MECC_TOT, max_ore, "FAST")
    if not est:
        return None, None

    if vel and est["ore_tot"] < vel["ore_tot"]:
        return est, "TEMPO"
    if eco and est["cost"] < eco["cost"]:
        return est, "COSTO"

    return None, None

# ============================================================
# STAMPA RISULTATI
# ============================================================

def stampa(titolo, soluzione, target, budget, ettari, mostra_interni_esterni):
    pot_mecc = soluzione["num_meccanizzati"] * RESA_MECC * soluzione["ore_mecc"]
    pot_man = soluzione["num_manuali"] * RESA_MANUALE * soluzione["ore_manual"]

    eff_mecc = min(target, pot_mecc)
    eff_man = min(max(0, target - eff_mecc), pot_man)

    print("\n" + "=" * 78)
    print(titolo.center(78))
    print("=" * 78)

    if mostra_interni_esterni:
        print(f"{'Operatori manuali interni':35s}{min(soluzione['num_manuali'],10):>5d}  | ore {soluzione['ore_manual']:>3d}")
        print(f"{'Operatori meccanizzati interni':35s}{min(soluzione['num_meccanizzati'],10):>5d}  | ore {soluzione['ore_mecc']:>3d}")
        print(f"{'Operatori manuali esterni':35s}{max(0,soluzione['num_manuali']-10):>5d}  | ore {soluzione['ore_manual'] if soluzione['num_manuali']>10 else 0:>3d}")
        print(f"{'Operatori meccanizzati esterni':35s}{max(0,soluzione['num_meccanizzati']-10):>5d}  | ore {soluzione['ore_mecc'] if soluzione['num_meccanizzati']>10 else 0:>3d}")
    else:
        print(f"{'Operatori manuali':35s}{soluzione['num_manuali']:>5d}  | ore {soluzione['ore_manual']:>3d}")
        print(f"{'Operatori meccanizzati':35s}{soluzione['num_meccanizzati']:>5d}  | ore {soluzione['ore_mecc']:>3d}")

    print("\nPRODUZIONE")
    print("-" * 78)
    print(f"{'Produzione manuale':35s}{eff_man:>10.2f}  ton")
    print(f"{'Produzione meccanizzata':35s}{eff_mecc:>10.2f}  ton")
    print(f"{'Produzione totale':35s}{eff_man + eff_mecc:>10.2f}  ton")

    print("\nCOSTI")
    print("-" * 78)
    print(f"{'Budget disponibile':35s}{budget:>10.2f}  €")
    print(f"{'Costo totale':35s}{soluzione['cost']:>10.2f}  €")
    print(f"{'Tempo totale':35s}{soluzione['ore_tot']:>10d}  h")

    print("\nDETTAGLIO COSTI")
    print("-" * 78)

    if mostra_interni_esterni:
        man_int = min(soluzione["num_manuali"], 10)
        man_ext = max(0, soluzione["num_manuali"] - 10)
        mec_int = min(soluzione["num_meccanizzati"], 10)
        mec_ext = max(0, soluzione["num_meccanizzati"] - 10)

        print(f"{'Salari manuali interni':35s}{man_int*SAL_MAN_INT*soluzione['ore_manual']:>10.2f}  €")
        print(f"{'Salari meccanizzati interni':35s}{mec_int*SAL_MECC_INT*soluzione['ore_mecc']:>10.2f}  €")
        print(f"{'Salari manuali esterni':35s}{man_ext*SAL_MAN_EXT*soluzione['ore_manual']:>10.2f}  €")
        print(f"{'Salari meccanizzati esterni':35s}{mec_ext*SAL_MECC_EXT*soluzione['ore_mecc']:>10.2f}  €")

        if mec_ext > 0 and soluzione["ore_mecc"] > 0:
            print(f"{'Affitto macchine esterne':35s}{mec_ext*AFFITTO_MECC_EXT*soluzione['ore_mecc']:>10.2f}  €")
    else:
        print(f"{'Salari manuali':35s}{soluzione['num_manuali']*SAL_MAN_INT*soluzione['ore_manual']:>10.2f}  €")
        print(f"{'Salari meccanizzati':35s}{soluzione['num_meccanizzati']*SAL_MECC_INT*soluzione['ore_mecc']:>10.2f}  €")

    if soluzione["num_meccanizzati"] > 0 and soluzione["ore_mecc"] > 0:
        print(f"{'Carburante macchinari':35s}{CARB_HA*ettari*soluzione['num_meccanizzati']:>10.2f}  €")
        print(f"{'Manutenzione macchine (interne)':35s}{MANUT_HA*ettari*min(soluzione['num_meccanizzati'],10):>10.2f}  €")

    print("=" * 78)

# ============================================================
# MAIN
# ============================================================

def main():
    random.seed()

    ettari = {}
    rese = {}
    target_crop = {}

    print("Inserisci gli ettari per ciascun campo (0 se non presente).")
    for crop, (lo, hi) in CROPS.items():
        ha = float(input(f"- Ettari {crop}: ").replace(",", "."))
        ettari[crop] = ha
        rese[crop] = random.uniform(lo, hi)
        target_crop[crop] = ha * rese[crop]

    ett_tot = sum(ettari.values())
    target_tot = sum(target_crop.values())

    print("\nRESE CASUALI PER CAMPO")
    print("-" * 78)
    for crop in CROPS:
        print(f"{crop:15s} | Ettari: {ettari[crop]:6.2f} | Resa: {rese[crop]:6.2f} t/ha | Totale: {target_crop[crop]:8.2f} t")
    print("-" * 78)
    print(f"{'Totale ettari':25s}{ett_tot:10.2f} ha")
    print(f"{'Totale da raccogliere':25s}{target_tot:10.2f} t")

    while True:
        budget = float(input("\nInserisci il budget massimo (euro): ").replace(",", "."))
        max_ore = int(input("Inserisci il tempo massimo per la raccolta (ore): "))

        vel, eco = trova_interne(target_tot, budget, ett_tot, max_ore)
        est, motivo = trova_esterni(target_tot, budget, ett_tot, vel, eco, max_ore)

        if vel or eco or est:
            if vel:
                stampa("SOLUZIONE PIÙ VELOCE CON OPERATORI INTERNI", vel, target_tot, budget, ett_tot, False)
            else:
                print("\nNessuna soluzione trovata (solo interni).")

            if eco:
                stampa("SOLUZIONE PIÙ ECONOMICA CON OPERATORI INTERNI", eco, target_tot, budget, ett_tot, False)

            if est:
                print(f"\nConviene ingaggiare operatori esterni per motivo di: {motivo}".center(78))
                stampa("SOLUZIONE CON OPERATORI ESTERNI", est, target_tot, budget, ett_tot, True)

            break

        if input("\nBudget/tempo insufficienti. Riprovo? s/n: ").lower() != "s":
            print("\nProgramma terminato.")
            return
main()
input("\nPremi INVIO per uscire...")

