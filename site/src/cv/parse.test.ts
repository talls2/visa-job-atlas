import { describe, expect, it } from "vitest";
import skillsJson from "../../../knowledge/skills.json";
import type { Skill } from "../types";
import { experienceYears, findCerts, findLanguages, highestDegree, levelFromYears, parseCv } from "./parse";
import { jobFamily } from "./family";

const SKILLS = (skillsJson as { skills: Skill[] }).skills;
const NOW = new Date(2026, 9, 19);

const CV_EN = `Jane Doe
Backend Engineer
Summary
Backend developer with Python, Django and PostgreSQL on AWS.
Experience
Senior Backend Engineer, Acme Corp
Jan 2022 - Present
Built REST APIs in Python and Go, deployed with Docker and Kubernetes.
Software Developer, Beta Ltd
03/2019 - 12/2021
Java and Spring Boot microservices.
Education
B.Sc. Computer Science, State University
2015 - 2019
Certifications
AWS Certified Solutions Architect – Associate
Languages
English – Fluent
Spanish – Intermediate (B1)`;

const CV_PT = `Fulano de Tal
Desenvolvedor Full Stack
Experiência Profissional
Desenvolvedor Pleno - Empresa X
mar. de 2021 - atual
React, TypeScript e Node.js.
Estagiário de Desenvolvimento - Empresa Y
jan 2020 - fev 2021
Formação Acadêmica
Bacharelado em Ciência da Computação
2016 - 2020
Idiomas
Português - Nativo
Inglês - Avançado`;

describe("experience", () => {
  it("merges ranges and ignores education dates", () => {
    // Jan 2022 to Oct 2026 = 58 months, Mar 2019 to Dec 2021 = 34 months
    expect(experienceYears(CV_EN, NOW)).toBeCloseTo(7.7, 1);
  });
  it("reads Portuguese months and 'atual'", () => {
    expect(experienceYears(CV_PT, NOW)).toBeCloseTo(6.8, 1);
  });
});

describe("parseCv", () => {
  const p = parseCv(CV_EN, SKILLS, NOW);
  it("finds skills", () => {
    for (const s of ["python", "django", "postgres", "aws", "go", "docker", "kubernetes", "java", "spring"]) expect(p.skills).toContain(s);
    expect(p.skills).not.toContain("javascript");
  });
  it("reads degree, certs, languages and family", () => {
    expect(p.degree).toBe("bachelor");
    expect(p.certs).toContain("AWS Certified");
    expect(p.languages).toEqual(expect.arrayContaining([{ code: "en", level: "fluent" }, { code: "es", level: "intermediate" }]));
    expect(p.families[0]).toBe("software");
    expect(p.level).toBe("senior");
  });
  it("handles a Portuguese CV", () => {
    const q = parseCv(CV_PT, SKILLS, NOW);
    expect(q.degree).toBe("bachelor");
    expect(q.skills).toEqual(expect.arrayContaining(["react", "typescript", "node"]));
    expect(q.languages).toEqual(expect.arrayContaining([{ code: "pt", level: "native" }, { code: "en", level: "fluent" }]));
    expect(q.families[0]).toBe("software");
  });
});

describe("helpers", () => {
  it("degrees", () => {
    expect(highestDegree("MSc in Data Science")).toBe("master");
    expect(highestDegree("Tecnólogo em Análise e Desenvolvimento de Sistemas")).toBe("technical");
    expect(highestDegree("Self-taught developer")).toBe("none");
  });
  it("certs", () => {
    expect(findCerts("OSCP, CompTIA Security+ and CKA")).toEqual(expect.arrayContaining(["OSCP", "CompTIA Security+", "CKA"]));
  });
  it("languages default levels", () => {
    expect(findLanguages("Languages: German")).toEqual([{ code: "de", level: "intermediate" }]);
  });
  it("levels", () => {
    expect(levelFromYears(0.5)).toBe("entry");
    expect(levelFromYears(3)).toBe("mid");
    expect(levelFromYears(10)).toBe("lead");
  });
  it("families match the pipeline", () => {
    expect(jobFamily("Senior Product Security Engineer")).toBe("security");
    expect(jobFamily("Machine Learning Engineer")).toBe("data");
    expect(jobFamily("Software Engineer in Test")).toBe("qa");
    expect(jobFamily("Senior Product Manager, Security")).toBe("product");
    expect(jobFamily("Softwareentwickler Java (m/w/d)")).toBe("software");
    expect(jobFamily("Solutions Engineer")).toBeNull();
    expect(jobFamily("Mechanical Engineer")).toBeNull();
    expect(jobFamily("Video Editor, Marketing")).toBe("video");
    expect(jobFamily("Editor de Vídeo")).toBe("video");
    expect(jobFamily("Senior Motion Designer")).toBe("video");
    expect(jobFamily("Graphic Designer")).toBe("design");
    expect(jobFamily("Hardware Designer")).toBeNull();
    expect(jobFamily("Senior Learning Designer")).toBeNull();
    expect(jobFamily("Recruiter, Design")).toBeNull();
  });
});

const CV_VIDEO = `Marina Costa
Editora de Vídeo e Motion Designer
Experiência Profissional
Editor de Vídeo - Agência Exemplo
mai 2021 - atual
Edição no Premiere Pro e DaVinci Resolve, motion graphics no After Effects, color grading.
Designer Gráfico - Estúdio Exemplo
fev 2019 - abr 2021
Identidade visual e branding no Illustrator e Photoshop.
Formação Acadêmica
Bacharelado em Design
2015 - 2018
Idiomas
Português - Nativo
Inglês - Intermediário`;

describe("creative CVs", () => {
  it("detects a video editor", () => {
    const p = parseCv(CV_VIDEO, SKILLS, NOW);
    expect(p.families[0]).toBe("video");
    expect(p.skills).toEqual(expect.arrayContaining(["premiere-pro", "davinci-resolve", "after-effects", "motion-graphics", "color-grading", "illustrator", "photoshop", "branding"]));
    expect(p.degree).toBe("bachelor");
  });
});
