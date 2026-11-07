# Private website preview

1. On the repository page, choose **Code → Codespaces → Create codespace on master**.
2. Wait for the environment to finish starting. The preview server starts automatically.
3. In **Ports**, open port **4000** and keep **Port Visibility → Private**.

The preview uses root-relative asset URLs and works without publishing GitHub Pages.
Startup messages are written to `/tmp/zeyu-homepage-preview.log` inside the codespace.
If an existing codespace uses an older configuration, run **Codespaces: Rebuild Container**.

Normal commits only build the website. Public publishing requires manually running
the Pages workflow and explicitly selecting its **Publish this website publicly on GitHub Pages** option.
To remove the already-published website, use **Settings → Pages → Unpublish site**.
Preview privacy does not change repository visibility; source files in a public repository remain public.
