# Red-Blue: how we work together

## The setup
- `main` is the shared, working version. It is protected, so nobody can push to it directly.
- Ryan works on branch `mindel`. Henry works on branch `fricke`.
- Everything reaches main through a **pull request (PR)**, and the other person has to approve it.

## Your routine
1. **Start of each session:** pull the latest main into your branch.
   ```
   git checkout <your-branch>
   git pull origin main
   ```
2. **Work and save:**
   ```
   git add -A
   git commit -m "short description"
   git push origin <your-branch>
   ```
3. **When a piece of work is ready:** open a PR from your branch into main. Use the banner on the GitHub repo page, or `gh pr create --base main --fill`.
4. **The other person reviews it:** open the PR, then Files changed, then Review changes, then Approve.
5. **Merge it:** click "Merge pull request" once it is approved. Then both of us pull main into our branches again (step 1).

## Rules
- You can't approve your own PR, so the other person always reviews.
- Keep PRs small and merge every day or two, so branches don't drift apart.
- If a PR says "has conflicts," run `git pull origin main` on your branch, fix the marked lines, commit, and push. The PR updates itself.
- Don't edit the same files at the same time without talking first.

## Who owns what (from the plan)
- Henry: backend, API, grading logic, data model.
- Ryan: frontend, PWA, skill tree, lesson screens.
- Both: the challenge schema and data model, before we split up.

See [docs/PLAN.md](docs/PLAN.md) for what we are building.
