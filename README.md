<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/jotpio/behavior_HF">
    <img src="images/fishmodel3.jpg" alt="Logo" width="80" height="120">
  </a>

<h3 align="center">RoboFish at HF</h3>

  <p align="center">
    Code base of the RoboFish exhibit at Humboldt Forum 
    <br />
    <br />
    <a href="https://github.com/jotpio/behavior_HF/issues">Report Bug</a>
    ·
    <a href="https://github.com/jotpio/behavior_HF/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This project is part of my master's thesis "Exploration of human leading behavior using a controlled biomimetic robot in a simulated fish tank". This repository contains the fish simulation and robot control. 
The simulation is based on the behavior model presented by Couzin et al.   [![DOI:10.1006/jtbi.2002.3065](https://zenodo.org/badge/DOI/10.1006/jtbi.2002.3065.svg)](https://doi.org/10.1006/jtbi.2002.3065)
<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
* [![Made withJupyter](https://img.shields.io/badge/Made%20with-Jupyter-orange?style=for-the-badge&logo=Jupyter)](https://jupyter.org/try)


<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

This is an example of how to list things you need to use the software and how to install them.
* install Python 3.9.5
* install git

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/jotpio/behavior_HF.git
   ```
2. Install pip packages using setup.py
   ```sh
   python setup.py install 
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

The `main_challenge_simulation.py` simulates the challenge in the Humboldt Forum. Use it if you intend to run it locally as it does not connect to the other software components.
Run the it by executing:
   ```sh
   python main_challenge_simulation.py
   ```

The `main_simulation.py` is the startup for the simulation in the Humboldt Forum exhibit. It connects to the other software components.
Run the it by executing:
   ```sh
   python main_simulation.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg

See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Jonas Piotrowski - marc.jonas.piotrowski@gmail.com

Project Link: [https://github.com/jotpio/behavior_HF](https://github.com/jotpio/behavior_HF)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [David James](https://www.igb-berlin.de/profile/david-james)
* [David Bierbach](https://www.igb-berlin.de/profile/david-bierbach)
* [Dustin Lehmann](https://www.tu.berlin/control/user-dlehmann)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/jotpio/behavior_HF.svg?style=for-the-badge
[contributors-url]: https://github.com/jotpio/behavior_HF/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/jotpio/behavior_HF.svg?style=for-the-badge
[forks-url]: https://github.com/jotpio/behavior_HF/network/members
[stars-shield]: https://img.shields.io/github/stars/jotpio/behavior_HF.svg?style=for-the-badge
[stars-url]: https://github.com/jotpio/behavior_HF/stargazers
[issues-shield]: https://img.shields.io/github/issues/jotpio/behavior_HF.svg?style=for-the-badge
[issues-url]: https://github.com/jotpio/behavior_HF/issues
[license-shield]: https://img.shields.io/github/license/jotpio/behavior_HF.svg?style=for-the-badge
[license-url]: https://github.com/jotpio/behavior_HF/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/jonas-piotrowski
[product-screenshot]: images/screenshot.png

[![forthebadge cc-by](http://ForTheBadge.com/images/badges/cc-by.svg)](https://creativecommons.org/licenses/by/4.0)
[![licensebuttons by](https://licensebuttons.net/l/by/3.0/88x31.png)](https://creativecommons.org/licenses/by/4.0)