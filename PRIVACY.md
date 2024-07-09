# Privacy and Security Notice

*Last updated: 2023-11-22 (YYYY-MM-DD)*

> **Notice**
> 
> This is not intended to be a legally binding document. It is only for informing you of the privacy implications of using Shatter.

Shatter does not collect any personal information itself, and we don't want it to. However, to provide some features of the software, we might need to do things that present a privacy risk. The features are listed below along with the possible risks they present.

If a feature presents a possible risk to your privacy, you can always turn it off by going to `Edit` → `Preferences` → `Addons` → `Shatter` and disabling it under the "Network and privacy" section.

## Update Checking

Update checking pulls an update info file from GitHub's servers. We are not able to log downloads as we do not have access to GitHub logs as of writing, but GitHub may be able to. Please check and agree to their [Privacy Statement](https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement) when using the updater.

This might harm your privacy in a few different ways:

* GitHub could log your request, which might include your OS type, IP address, geographic location, time, path of the requested data and maybe more.
* Someone may be able to notice that you are trying to connect to GitHub, which may be suspicious in your region or life situation.

## Automatic Updates

Automatic updates require update checking, but also download an update file that can be hosted on any server. At the moment, we use GitHub for this, so there are similar privacy implications to update checking, though you should also note the following cases:

* If a Shatter developer's GitHub account is hacked and private signing keys are stolen, an attacker may be able to install malware like a keylogger or password stealer which can greatly harm your privacy.
* A Shatter developer may be coerced or pressured into including malware with a Shatter update.

Due to this, we recommend that you run up-to-date antivirus software. If you feel that you may be vulnerable to attack, you should disable automatic update installation and manually check each update for malware.

Also, please note that automatic updates are enabled by default and the check will load when Shatter is started. If you want to disable updates before you install, please disconnect your PC from the internet before installing and enabling Shatter, then disable the updater, then connect your PC to the internet again.

## Security of Updates

We use RSA-based digital signatures to help ensure that update info and update install files come from the Shatter authors and not an unknown source, such as someone who has hacked into an account but does not have access to a developer's private key.

With that said, digital signatures are not foolproof. For example, if someone is able to find the private key of a developer (either via hacking or tricking the developer or attacking the digital signature scheme itself) they may be able to sign an update to make it appear as if it came from the Shatter developers even though it did not.

If you would like to learn more about digital signatures and their limitations, the [Wikipedia article on Digital signatures](https://en.wikipedia.org/wiki/Digital_signature) is a good place to start.

## Quick Test

The quick test server works by creating a web server that a client then loads levels from. While we have tried to make this web server secure, it may turn out to have vulnerabilities that crash the server or even allow it to run code remotely.

Normally, this server is only accessible on your local network and not to anyone else, so the impact of this is limited. If your router is configured to route port 8000 on your PC to the outside world, however, these possible issues present a major security and privacy risk. If you think this port may be exposed, then you should check that your router is blocking incoming connections to the port on your PC.

## Historical Features

We have previously created other features that may present a privacy and security risk, but that have been removed in new versions. Please update to the latest version of Shatter which this document applies to.

## Reporting Security Issues

If you find a security issue and want to disclose it privately, you can contact one of the following:

* **Knot126 via Email**: cddepppp256 \[AT\] gmail \[DOT\] com
