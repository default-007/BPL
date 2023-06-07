window.onload = function () {
	Particles.init({
		selector: ".background",
	});
};
const particles = Particles.init({
	selector: ".background",
	color: ["#03dac6", "#ff0266", "#F49D1A"],
	connectParticles: true,
	responsive: [
		{
			breakpoint: 768,
			options: {
				color: ["#03dac6", "#ff0266", "#F49D1A"],
				maxParticles: 43,
				connectParticles: false,
			},
		},
	],
});

/* Credit and Thanks:
Matrix - Particles.js;
SliderJS - Ettrics;
Design - Sara Mazal Web;
Fonts - Google Fonts
*/
// function([string1, string2],target id,[color1,color2])
consoleText(
	["Build Your Brand.", "Create Your Identity", "Grow Your Business."],
	"text",
	["#03dac6", "#faebd7", "#ff0266"]
);

function consoleText(words, id, colors) {
	if (colors === undefined) colors = ["#F49D1A"];
	var visible = true;
	var con = document.getElementById("console");
	var letterCount = 1;
	var x = 1;
	var waiting = false;
	var target = document.getElementById(id);
	target.setAttribute("style", "color:" + colors[0]);
	window.setInterval(function () {
		if (letterCount === 0 && waiting === false) {
			waiting = true;
			target.innerHTML = words[0].substring(0, letterCount);
			window.setTimeout(function () {
				var usedColor = colors.shift();
				colors.push(usedColor);
				var usedWord = words.shift();
				words.push(usedWord);
				x = 1;
				target.setAttribute("style", "color:" + colors[0]);
				letterCount += x;
				waiting = false;
			}, 1000);
		} else if (letterCount === words[0].length + 1 && waiting === false) {
			waiting = true;
			window.setTimeout(function () {
				x = -1;
				letterCount += x;
				waiting = false;
			}, 1000);
		} else if (waiting === false) {
			target.innerHTML = words[0].substring(0, letterCount);
			letterCount += x;
		}
	}, 120);
	window.setInterval(function () {
		if (visible === true) {
			con.className = "console-underscore hidden";
			visible = false;
		} else {
			con.className = "console-underscore";

			visible = true;
		}
	}, 400);
}
