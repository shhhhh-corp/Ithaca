# Ithaca

## What is this?
This Github action helps you stay on top of things in your CICD.

## Usage
In your relevant github action job, add

``` yaml
    - name: shhhhh corp
      uses: shhhhh-corp/Ithaca@v0.8.3
```

### Parameters
This action can work just fine as is, but can be customized with the
following parameters:

#### `github_token`
This token is needed to inspect the repository. By default, it gets a
special token created for the active Github Action. See
https://docs.github.com/en/actions/reference/authentication-in-a-workflow
for more details.

#### `cause_build_to_fail`
When an issue is found, would you like this action to result in
causing the job/build to fail? The default is `false`, but if you'd
like this feature, just add the following snippet, INSTEAD of the one above:

``` yaml
    - name: shhhhh corp
      uses: shhhhh-corp/Ithaca@v0.7.8
      with:
          cause_build_to_fail: true
```

### Jira integration
To enable Jira integration, add the following 3 environment variables:

``` yaml
    - name: shhhhh corp
        uses: shhhhh-corp/Ithaca@v0.8.2
        env:
          JIRA_URL: ${{ secrets.JIRA_URL }}
          JIRA_ACCESS_USER: ${{ secrets.JIRA_ACCESS_USER }}
          JIRA_ACCESS_PW: ${{ secrets.JIRA_ACCESS_PW }}
```

#### Example values
`JIRA_URL=https://acme.atlassian.net`
`JIRA_ACCESS_USER=myemail@acme.io`
`JIRA_ACCESS_PW=letmein`
