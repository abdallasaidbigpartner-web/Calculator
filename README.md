# Ultimate Calculator

**A scientific, algebra and calculus calculator for Android, designed, coded and built entirely on a phone.**

![Build](https://github.com/abdallasaidbigpartner-web/Calculator/actions/workflows/build.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Platform: Android](https://img.shields.io/badge/platform-Android%205.0%2B-3ddc84)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Kivy](https://img.shields.io/badge/UI-Kivy-orange)

Created by **[Abdalla Said Ahmed](https://github.com/abdallasaidbigpartner-web)**

---

## Download

1. Open the **[Releases page](https://github.com/abdallasaidbigpartner-web/Calculator/releases/latest)** on your Android phone.
2. Under **Assets**, tap `UltimateCalculator-....apk` to download it.
3. Open the downloaded file and tap **Install**.
   If Android blocks it, tap **Settings** and allow installs from your browser or file manager, then go back and install.
4. If Play Protect shows a warning, choose **Install anyway**. The app is not on the Play Store and is signed with a debug key.

**Requirements:** Android 5.0 or newer on a 64-bit (arm64) phone, which covers almost every phone sold in the last several years. The app works fully offline and has no ads, accounts or tracking.

<!-- Add real screenshots here after you take them on your phone:
![Calculate screen](docs/screenshots/calculate.png)
-->

---

## Features

| Area | What you get |
| --- | --- |
| **Calculate** | Brackets, percent, Ans, UNDO, 2nd key, DEG/RAD, fraction or decimal answers (S<>D), history of the last 50 results |
| **Variables and memory** | x, y, z, A, B, C with STO, plus MC, MR, M+, M- |
| **Functions** | sin, cos, tan, hyperbolic and inverse forms, sec, csc, cot, log, ln, log base b, roots, powers, rounding, random numbers |
| **Algebra (CAS)** | Solve equations, expand, factor and simplify polynomials, exact symbolic derivative and integral of polynomials |
| **Calculus** | Numeric derivative, definite integral, limits, sums (Σ) and products (Π) |
| **Complex numbers** | `i`, Re, Im, conjugate, arg, and results like `2i` or `5 + 5i` |
| **Number theory and bits** | n!, nCr, nPr, Mod, GCD, LCM, prime factorisation, AND, OR, XOR, NOT, shifts, BIN, HEX, OCT |
| **Matrices and vectors** | Determinant, inverse, transpose, multiply, solve linear systems, dot product, cross product, norm |
| **Statistics** | Mean, median, standard deviation, variance, linear regression, normal, binomial and Poisson distributions |
| **Convert** | Length, mass, time, area, volume, speed, energy, pressure, data and temperature |
| **Constants** | Speed of light, gravity, Planck, Avogadro, Boltzmann, electron charge and more |
| **Graph and Table** | Plot any formula in x with zoom and pan, or view a table of values |

---

## How to use it

Type with the keys, then press `=`. Use the tabs (**f(x)**, **CAS**, **Num**, **Stat**, **Conv**, **Const**) to reach more functions, and the **2nd** key for the alternate label shown on many keys.

| You enter | Result |
| --- | --- |
| `2π` | `6.28318530718` |
| `sin(30)` in DEG mode | `0.5` |
| `x^2-5x+6=0` | `x = 2,   x = 3` |
| `factor(x^2-9)` | `(x - 3)(x + 3)` |
| `expand((x+1)^3)` | `x^3 + 3x^2 + 3x + 1` |
| `diff(x^3+2x,2)` | `14` |
| `integ(sin(x),0,π)` | `2` |
| `sigma(x,1,100)` | `5050` |
| `lim(sin(x)÷x,0)` | `1` |
| `√(-4)` | `2i` |
| `det([[1,2],[3,4]])` | `-2` |
| `linsolve([[2,1],[1,3]],[3,5])` | `[0.8, 1.4]` |
| `mean([1,2,3,4])` | `2.5` |
| `ncr(5,2)` | `10` |
| `prime(60)` | `2^2 × 3 × 5` |
| `conv(5,"km","mi")` | `3.10685596119` |
| `bin(10)` | `0b1010` |

Tips: the `x` key is in the strip under the display. Unit keys on the **Conv** tab add the quote marks for you. Calculus functions always work in radians. Equation solving searches x from -100 to 100 unless the equation is a polynomial, where all roots (including complex ones) are found.

---

## Built on a phone

This whole project was made without a computer: the code was written and managed from an Android phone using **Termux**, and the APK is built for free by **GitHub Actions** in the cloud.

```
Termux (write and push code)  ->  GitHub  ->  GitHub Actions (Buildozer)  ->  APK  ->  install on phone
```

### Build your own app the same way

1. **Install Termux** from F-Droid or its GitHub page (the Play Store version is outdated).
2. **Create a free GitHub account**, then a new **public** repository.
3. **Add three things to the repository:**
   - `main.py`, your Kivy app
   - `buildozer.spec`, the app settings (see below)
   - `.github/workflows/build.yml`, the build recipe
4. **Push from Termux:**
   ```
   pkg update && pkg install -y git
   git clone https://github.com/YOUR-NAME/YOUR-REPO.git
   cd YOUR-REPO
   git add . && git commit -m "My app" && git push
   ```
   GitHub asks for a username and a **personal access token** (not your password). Create one in Settings, Developer settings, Personal access tokens (classic), with the `repo` and `workflow` permissions.
5. **Open the Actions tab.** The build starts by itself and takes about 10 to 25 minutes.
6. **Download the APK** from the run's Artifacts (or from Releases, see below) and install it.

Public repositories get free, unlimited GitHub Actions build minutes.

### Publishing a release for your followers

Artifacts need a GitHub login to download. Releases are public. To publish one, push a version tag:

```
git tag v1.0.0
git push origin v1.0.0
```

The workflow builds the APK and attaches it to a new release automatically.

### Key settings in `buildozer.spec`

```
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
```

### Problems we hit and how we fixed them

| Problem | Fix |
| --- | --- |
| `pip install kivy` fails inside Termux | Do not install Kivy in Termux. Build in the cloud instead. |
| The Docker-based Buildozer action fails | Run Buildozer directly in the workflow. |
| `possibly undefined macro: LT_SYS_SYMBOL_USCORE` | Install `automake` and `libltdl-dev`. |
| Kivy fails to compile on a very new Python | Pin Python 3.11 (`python3==3.11.5` in `requirements`). |
| `incompatible function pointer types` in Kivy C code | Pin the older Android NDK with `android.ndk = 25b`. |
| `Unsupported class file major version 69` | Gradle needs Java 17. Add `actions/setup-java` with Java 17. |
| Artifacts cannot be downloaded by others | Publish a Release (push a `v*` tag). |

---

## Under the hood

- **Language and UI:** Python 3.11 with the [Kivy](https://kivy.org) toolkit.
- **Packaging:** [Buildozer](https://github.com/kivy/buildozer) and [python-for-android](https://github.com/kivy/python-for-android).
- **Safe math engine:** expressions are parsed into a syntax tree and evaluated against a whitelist of functions. The app never calls Python's `eval`, so typed input cannot run arbitrary code.
- **Exact algebra for polynomials:** polynomials in x are detected and handled with exact fractions, which powers Expand, Factor, symbolic derivatives and integrals.
- **Testing:** the math engine was checked against more than 125 test expressions before release.

```
.
├── main.py                  the whole app: math engine and Kivy interface
├── buildozer.spec           Android build settings
├── .github/workflows/
│   └── build.yml            cloud build and release recipe
├── README.md
├── CHANGELOG.md
├── RELEASE_NOTES.md         text shown on each GitHub release
└── LICENSE
```

---

## Limitations and roadmap

**Current limits**
- Symbolic algebra works for polynomials in x only (no trigonometric or logarithmic symbolic algebra).
- No step-by-step solutions, currency conversion, spreadsheet or inequality solver.
- The APK is for 64-bit (arm64) phones and is debug-signed, not yet on the Play Store.

**Ideas for next versions**
- Full symbolic engine (SymPy) for general algebra and calculus
- Step-by-step solutions
- App icon, themes and landscape layout
- 32-bit phone support and a signed release build
- Currency conversion

---

## Contributing

Bug reports and ideas are welcome. Open an **Issue** and describe what you did, what you expected and what happened. Pull requests are welcome too: fork the repository, change `main.py`, and open a pull request. The build runs automatically, so you can check that the APK still builds.

If you like the project, please give it a **star** on GitHub and share it with a friend.

---

## License

Released under the **MIT License**. You may use, copy, modify and share this software, including commercially, as long as you keep the copyright notice. See [LICENSE](LICENSE).

## Acknowledgements

- The Kivy, Buildozer and python-for-android teams for the tools that make this possible.
- Casio ClassWiz, GeoGebra and Qalculate! for inspiration on what a complete calculator should include.
- Built with AI pair-programming help from Abdalla himself created.

**Created by Abdalla Said Ahmed.**
