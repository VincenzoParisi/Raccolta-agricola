import random
import math

# ============================================================
# COSTANTI GLOBALI
# ============================================================

RESA_MANUALE = 0.50         # tonnellate / ora prodotte da un operatore manuale
RESA_MECC = 1.5             # tonnellate /ora prodotte da un operatore interno meccanizzato

SAL_MAN_INT = 8.0           # salario orario degli operatori manuali interni
SAL_MECC_INT = 10.0         # salario orario degli operatori meccanizzati interni 
SAL_MAN_EXT = 10.0          # salario orario degli operatori manuali esterni
SAL_MECC_EXT = 12.0         # salario orario degli operatori meccanizzati esterni

CARB_HA = 18.0              # costo carburante per ettaro per ogni macchina interna
MANUT_HA = 8.0              # costo manutenzione per ettaro per ogni macchina interna

MAX_MAN_INT = 10            # massimo numero di operatori manuali interni
MAX_MECC_INT = 10           # massimo numero di operatori meccanizzati interni
MAX_MAN_EXT = 20            # massimo numero di operatori manuali esterni
MAX_MECC_EXT = 20

AFFITTO_MECC_EXT = 25.0     # costo orario per ogni macchina esterna utilizzata

SCARTI = {                  # scarti per singola coltura
    "Orzo": 0.10,
    "Avena": 0.12,
    "Frumento": 0.15,
}

CROPS = {                   # rese casuali per ettaro di ogni coltura (range min, range max)
    "Orzo": (20.0, 25.0),
    "Avena": (18.0, 25.0),
    "Frumento": (25.0, 30.0),
}

# ============================================================
# FUNZIONI DI SUPPORTO
# ============================================================

def ore_necessarie(ton, resa_oraria):
    return int(math.ceil(ton / resa_oraria - 1e-12))

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

def costo_dettagliato(num_manuali, num_meccanizzati, ore_manual, ore_mecc, ettari):
    ore_tot = max(ore_manual, ore_mecc)

    costo_or = costo_orario(num_manuali, num_meccanizzati) * ore_tot
    carburante = num_meccanizzati * CARB_HA * ettari
    manut = min(num_meccanizzati, MAX_MECC_INT) * MANUT_HA * ettari

    affitto = 0
    if num_meccanizzati > MAX_MECC_INT:
        affitto = (num_meccanizzati - MAX_MECC_INT) * AFFITTO_MECC_EXT * ore_mecc

    totale = costo_or + carburante + manut + affitto
    return costo_or, carburante, manut, affitto, totale

# ============================================================
# RICERCA SOLUZIONI
# ============================================================

def trova_soluzione(target, budget, ettari, max_man, max_mecc, max_ore, priorita):
    soluzioni = []

    for man in range(max_man + 1):
        for mec in range(max_mecc + 1):
            if man == 0 and mec == 0:
                continue

            for ore_mecc in range(max_ore + 1 if mec > 0 else 1):
                ton_mecc = mec * RESA_MECC * ore_mecc
                restante = target - ton_mecc

                if restante <= 0:
                    ore_man = 0
                    man_eff = 0
                else:
                    if man == 0:
                        continue
                    man_eff = man
                    ore_man = ore_necessarie(restante, man_eff * RESA_MANUALE)
                    if ore_man > max_ore:
                        continue

                ore_tot = max(ore_man, ore_mecc)
                if ore_tot > max_ore:
                    continue

                _, _, _, _, costo = costo_dettagliato(man_eff, mec, ore_man, ore_mecc, ettari)
                if costo > budget:
                    continue

                soluzioni.append({
                    "num_manuali": man_eff,
                    "num_meccanizzati": mec,
                    "ore_manual": ore_man,
                    "ore_mecc": ore_mecc,
                    "ore_tot": ore_tot,
                    "cost": costo
                })

    if not soluzioni:
        return None

    if priorita == "FAST":
        return min(soluzioni, key=lambda s: (s["ore_tot"], s["cost"]))
    else:
        return min(soluzioni, key=lambda s: (s["cost"], s["ore_tot"]))

# ============================================================
# STAMPA CONFRONTO SOLUZIONI
# ============================================================

def stampa_confronto(crop, vel, eco, est, target, budget, ettari):
    print("\n" + "="*78)
    print(f"CONFRONTO SOLUZIONI - {crop.upper()}".center(78))
    print("="*78)

    print(f"{'Parametro':<28}{'Veloce':>15}{'Economica':>15}{'Esterna':>15}")
    print("-"*78)

    def split_ops(sol):
        if sol is None:
            return ("—","—","—","—")
        man = sol["num_manuali"]
        mec = sol["num_meccanizzati"]
        man_int = min(man, MAX_MAN_INT)
        man_ext = max(0, man - MAX_MAN_INT)
        mec_int = min(mec, MAX_MECC_INT)
        mec_ext = max(0, mec - MAX_MECC_INT)
        return (man_int, man_ext, mec_int, mec_ext)

    def get(sol, key):
        return "—" if sol is None else sol[key]

    def costi(sol):
        if sol is None:
            return ("—","—","—","—","—")
        c_or, carb, man, aff, tot = costo_dettagliato(
            sol["num_manuali"], sol["num_meccanizzati"],
            sol["ore_manual"], sol["ore_mecc"], ettari
        )
        return (f"{c_or:.2f}", f"{carb:.2f}", f"{man:.2f}", f"{aff:.2f}", f"{tot:.2f}")

    vel_ops = split_ops(vel)
    eco_ops = split_ops(eco)
    est_ops = split_ops(est)

    vel_c = costi(vel)
    eco_c = costi(eco)
    est_c = costi(est)

    print(f"{'Manuali interni':<28}{vel_ops[0]:>15}{eco_ops[0]:>15}{est_ops[0]:>15}")
    print(f"{'Manuali esterni':<28}{vel_ops[1]:>15}{eco_ops[1]:>15}{est_ops[1]:>15}")
    print(f"{'Meccanizzati interni':<28}{vel_ops[2]:>15}{eco_ops[2]:>15}{est_ops[2]:>15}")
    print(f"{'Meccanizzati esterni':<28}{vel_ops[3]:>15}{eco_ops[3]:>15}{est_ops[3]:>15}")

    print(f"{'Ore manuali':<28}{str(get(vel,'ore_manual')):>15}{str(get(eco,'ore_manual')):>15}{str(get(est,'ore_manual')):>15}")
    print(f"{'Ore meccanizzate':<28}{str(get(vel,'ore_mecc')):>15}{str(get(eco,'ore_mecc')):>15}{str(get(est,'ore_mecc')):>15}")
    print(f"{'Ore totali':<28}{str(get(vel,'ore_tot')):>15}{str(get(eco,'ore_tot')):>15}{str(get(est,'ore_tot')):>15}")

    print(f"{'Costo orario (€)':<28}{vel_c[0]:>15}{eco_c[0]:>15}{est_c[0]:>15}")
    print(f"{'Carburante (€)':<28}{vel_c[1]:>15}{eco_c[1]:>15}{est_c[1]:>15}")
    print(f"{'Manutenzione (€)':<28}{vel_c[2]:>15}{eco_c[2]:>15}{est_c[2]:>15}")
    print(f"{'Affitto esterni (€)':<28}{vel_c[3]:>15}{eco_c[3]:>15}{est_c[3]:>15}")
    print(f"{'Costo totale (€)':<28}{vel_c[4]:>15}{eco_c[4]:>15}{est_c[4]:>15}")

    print("="*78)

# ============================================================
# RIEPILOGO FINALE
# ============================================================

def riepilogo(soluzioni, target_crop, ettari, max_ore_tot, budget_tot):
    print("\n" + "="*78)
    print("RIEPILOGO FINALE".center(78))
    print("="*78)

    print(f"{'Coltura':<12}{'Tipo':<12}{'Ore totali':>12}{'Costo (€)':>15}")
    print("-"*78)

    totale_ore = 0
    totale_costo = 0

    max_man_int = 0
    max_mecc_int = 0
    max_man_ext = 0
    max_mecc_ext = 0

    for crop, dati in soluzioni.items():
        sol = dati["sol"]
        tipo = dati["tipo"]

        if sol is None:
            print(f"{crop:<12}{'—':<12}{'—':>12}{'—':>15}")
            continue

        man = sol["num_manuali"]
        mec = sol["num_meccanizzati"]

        man_int = min(man, MAX_MAN_INT)
        man_ext = max(0, man - MAX_MAN_INT)
        mec_int = min(mec, MAX_MECC_INT)
        mec_ext = max(0, mec - MAX_MECC_INT)

        max_man_int = max(max_man_int, man_int)
        max_man_ext = max(max_man_ext, man_ext)
        max_mecc_int = max(max_mecc_int, mec_int)
        max_mecc_ext = max(max_mecc_ext, mec_ext)

        ore = sol["ore_tot"]
        costo = sol["cost"]

        totale_ore += ore
        totale_costo += costo

        print(f"{crop:<12}{tipo:<12}{ore:>12}{costo:>15.2f}")

    print("-"*78)
    print(f"Totale ore: {totale_ore} / {max_ore_tot}")
    print(f"Totale costo: {totale_costo:.2f} € / {budget_tot:.2f} €")
    print("="*78)

# ============================================================
# MAIN 
# ============================================================

def main():
    random.seed()

    # --------------------------------------------------------
    # INSERIMENTO ETTARI E CALCOLO DELLE RESE
    # --------------------------------------------------------
    ettari = {}
    rese = {}
    target_crop = {}

    print("Inserisci gli ettari per ciascun campo:")
    for crop, (lo, hi) in CROPS.items():
        ha = float(input(f"- Ettari {crop}: "))
        ettari[crop] = ha
        resa = random.uniform(lo, hi)
        rese[crop] = resa
        target_crop[crop] = ha * resa * (1 - SCARTI[crop])

    tot_target = sum(target_crop.values())

    # --------------------------------------------------------
    # LOOP DI RIPETIZIONE PER BUDGET + ORE
    # --------------------------------------------------------
    while True:

        budget_tot = float(input("\nBudget totale (€): "))
        max_ore_tot = int(input("Ore totali massime: "))

        # ========================================================
        # RIPARTIZIONE ORE
        # ========================================================

        ore_per_crop = {}
        somma_ore = 0

        for crop in CROPS:
            quota = target_crop[crop] / tot_target
            ore_per_crop[crop] = max(1, int(max_ore_tot * quota))
            somma_ore += ore_per_crop[crop]

        if somma_ore > max_ore_tot:
            diff = somma_ore - max_ore_tot
            coltura_principale = max(target_crop, key=target_crop.get)
            ore_per_crop[coltura_principale] = max(1, ore_per_crop[coltura_principale] - diff)

        elif somma_ore < max_ore_tot:
            diff = max_ore_tot - somma_ore
            coltura_principale = max(target_crop, key=target_crop.get)
            ore_per_crop[coltura_principale] += diff

        # ========================================================
        # STAMPA RISORSE
        # ========================================================

        print("\n" + "="*78)
        print("RIPARTIZIONE RISORSE PER COLTURA".center(78))
        print("="*78)

        print(f"{'Coltura':<10}{'Resa t/ha':>12}{'Scarto %':>10}{'Netta t':>12}{'Quota %':>10}{'Ore':>8}{'Budget (€)':>15}")
        print("-"*78)

        for crop in CROPS:
            resa = rese[crop]
            scarto = SCARTI[crop] * 100
            netta = target_crop[crop]
            quota = netta / tot_target
            ore = ore_per_crop[crop]
            budget_crop = budget_tot * quota

            print(f"{crop:<10}{resa:>12.2f}{scarto:>10.1f}%{netta:>12.2f}{quota*100:>9.2f}%{ore:>8}{budget_crop:>15.2f}")

        print("-"*78)
        print(f"{'Totale':<10}{'':>12}{'':>10}{tot_target:>12.2f}{'100%':>10}{sum(ore_per_crop.values()):>8}{budget_tot:>15.2f}")
        print("="*78 + "\n")

        # ========================================================
        # CALCOLO SOLUZIONI
        # ========================================================

        soluzioni = {}

        for crop in CROPS:
            print(f"\n=== {crop.upper()} ===")

            quota = target_crop[crop] / tot_target
            budget_crop = budget_tot * quota
            max_ore_crop = ore_per_crop[crop]

            max_man_int_only = MAX_MAN_INT
            max_mecc_int_only = MAX_MECC_INT

            max_man_ext_ok = MAX_MAN_INT + MAX_MAN_EXT
            max_mecc_ext_ok = MAX_MECC_INT + MAX_MECC_EXT

            vel = trova_soluzione(
                target_crop[crop], budget_crop, ettari[crop],
                max_man_int_only, max_mecc_int_only, max_ore_crop, "FAST"
            )
            eco = trova_soluzione(
                target_crop[crop], budget_crop, ettari[crop],
                max_man_int_only, max_mecc_int_only, max_ore_crop, "CHEAP"
            )
            est = trova_soluzione(
                target_crop[crop], budget_crop, ettari[crop],
                max_man_ext_ok, max_mecc_ext_ok, max_ore_crop, "FAST"
            )

            if vel is None and eco is None and est is None:
                print(f"\nNessuna soluzione trovata per {crop}. Budget/ore insufficienti per completare la raccolta.")
                soluzioni[crop] = {"sol": None, "tipo": "—"}
                continue

            stampa_confronto(crop, vel, eco, est, target_crop[crop], budget_crop, ettari[crop])

            # ========================================================
            # SCELTA DELLA SOLUZIONE
            # ========================================================
            if eco:
                scelta = eco
                tipo_scelta = "ECONOMICA"
            elif vel:
                scelta = vel
                tipo_scelta = "VELOCE"
            else:
                scelta = est
                tipo_scelta = "ESTERNA"

            soluzioni[crop] = {
                "sol": scelta,
                "tipo": tipo_scelta
            }

        riepilogo(soluzioni, target_crop, ettari, max_ore_tot, budget_tot)

        # ========================================================
        # RIPETERE IL CALCOLO?
        # ========================================================
        scelta = input("\nVuoi reinserire SOLO budget e ore e rifare il calcolo? (s/n): ").strip().lower()
        if scelta != "s":
            print("Fine programma.")
            break

main()
