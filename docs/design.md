# Design Considerations

Having a living but written down design document helps a library grow
consistently over time.

## Initial Inspiration

Software design doesn't happen in a vacuum, nor does it stay still. Described
here are some existing systems that inspired the design of `repoproviders`,
written at the very start by the person who did the initial work (Yuvi). Some
of these aspects will change as the project evolves, but it is better for the
change to be intentional rather than accidental - hence this piece of documentation.

### Jupyter Projects Lineage

I designed `repoprovider` based on my experience
designing [binderhub](https://github.com/jupyterhub/binderhub/),
[repo2docker](https://github.com/jupyterhub/repo2docker), [repo2jupyterlite](https://github.com/jupyterlite/repo2jupyterlite/)
and [nbgitpuller](https://github.com/jupyterhub/nbgitpuller/). 3 out of these 4
projects have seen a lot of heavy use, have some overlapping functionality, and have
evolved to support many features over time, with many contributors. `repoproviders`
is an attempt to design a small, self contained library that can be used by
all these projects, as well as make the effort required to build new projects like
that much smaller. Often the reason for 'why is it like X?' is 'because we implemented
something like this via method A in binderhub, method B in repo2docker, and learnt
C through the process, so we are trying X now'.

Being able to replace many chunks of repo2docker and binderhub was an initial design goal.

### DNS

While DNS often gets (jokingly) [blamed](https://isitdns.com/) for outages, it has been a
pretty good system that's lasted a *really* long time, adapting to changes in the world around
it pretty well. The resolvers in repoproviders are particularly inspired by how DNS is used
in practice, and I encourage you to learn more about how DNS works to understand some of
the design decisions in repoproviders resolvers better.

## Strongly Typed

`repoproviders` is as strongly typed as possible. Not just to test for correctness
when writing, but at runtime too. Resolvers and Fetchers indicate what type of
things they can resolve or fetch via types. How sure a resolver is that something
exists is also denoted by types. We can stick to fairly new versions of python,
and rely on types wherever possible
